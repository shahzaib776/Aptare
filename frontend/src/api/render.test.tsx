import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";

import { FIRST_BULLET_ID, fixtureResume } from "../features/dev/fixtureResume";
import { withText } from "../features/dev/resumeText";
import { settle } from "../test/helpers";
import type { RenderResponse } from "./types";
import { useDebouncedValue, useRender } from "./render";

function rendered(pdfHash: string): RenderResponse {
  return { tex_hash: "t", pdf_hash: pdfHash, page_count: 1, last_page_fill: 0.5, text_map: {} };
}

function bodyOf(fetchMock: ReturnType<typeof vi.fn>, call: number): string {
  return String((fetchMock.mock.calls[call]?.[1] as RequestInit | undefined)?.body);
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("useDebouncedValue", () => {
  test("starts with the value it is given", () => {
    const { result } = renderHook(() => useDebouncedValue("a", 500));

    expect(result.current).toBe("a");
  });

  test("takes a new value only after the delay, counted from the last change", async () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 500), {
      initialProps: { v: "a" },
    });

    rerender({ v: "b" });
    await settle(300);
    rerender({ v: "c" });
    await settle(300);
    expect(result.current).toBe("a");

    await settle(200);
    expect(result.current).toBe("c");
  });
});

describe("useRender", () => {
  function setup(responses: Array<Promise<Response> | Response>) {
    const fetchMock = vi.fn();
    for (const response of responses) fetchMock.mockReturnValueOnce(Promise.resolve(response));
    vi.stubGlobal("fetch", fetchMock);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const view = renderHook(({ resume }) => useRender(resume), {
      wrapper,
      initialProps: { resume: fixtureResume },
    });
    return { fetchMock, ...view };
  }

  const edited = (text: string) => withText(fixtureResume, FIRST_BULLET_ID, text);

  test("renders the first resume at once, without waiting for the debounce", async () => {
    const { result, fetchMock } = setup([json(200, rendered("one"))]);

    await settle();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(JSON.parse(bodyOf(fetchMock, 0)).template_id).toBe("dense-single");
    expect(result.current.render?.pdf_hash).toBe("one");
    expect(result.current.isPending).toBe(false);
  });

  test("a burst of edits makes one request, for the last edit", async () => {
    const { result, rerender, fetchMock } = setup([
      json(200, rendered("one")),
      json(200, rendered("two")),
    ]);
    await settle();

    rerender({ resume: edited("a") });
    await settle(100);
    rerender({ resume: edited("ab") });
    await settle(100);
    rerender({ resume: edited("abc") });
    expect(result.current.isPending).toBe(true);
    await settle(500);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(bodyOf(fetchMock, 1)).toContain("abc");
    expect(result.current.render?.pdf_hash).toBe("two");
    expect(result.current.isPending).toBe(false);
  });

  test("keeps showing the previous render while the next one compiles", async () => {
    let finish: (response: Response) => void = () => {};
    const slow = new Promise<Response>((resolve) => (finish = resolve));
    const { result, rerender } = setup([json(200, rendered("one")), slow]);
    await settle();

    rerender({ resume: edited("new") });
    await settle(500);

    expect(result.current.isCompiling).toBe(true);
    expect(result.current.render?.pdf_hash).toBe("one");

    await act(async () => finish(json(200, rendered("two"))));
    await settle();
    expect(result.current.render?.pdf_hash).toBe("two");
    expect(result.current.isCompiling).toBe(false);
  });

  test("a failed compile keeps the previous render and reports the error", async () => {
    const failure = {
      error: { code: "compile_failed", message: "Did not compile.", details: null },
    };
    const { result, rerender } = setup([json(200, rendered("one")), json(422, failure)]);
    await settle();

    rerender({ resume: edited("broken") });
    await settle(500);

    expect(result.current.render?.pdf_hash).toBe("one");
    expect(result.current.error?.message).toBe("Did not compile.");
  });

  test("going back to a resume that was already rendered does not compile again", async () => {
    const { rerender, fetchMock } = setup([json(200, rendered("one")), json(200, rendered("two"))]);
    await settle();
    rerender({ resume: edited("other") });
    await settle(500);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    rerender({ resume: fixtureResume });
    await settle(500);

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
