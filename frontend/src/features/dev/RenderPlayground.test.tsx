import { act, fireEvent, screen } from "@testing-library/react";

import type { RenderResponse } from "../../api/types";
import { loadPdf, type PdfDocument } from "../../components/pdf/pdfjs";
import { renderWithQuery, settle } from "../../test/helpers";
import { FIRST_BULLET_ID } from "./fixtureResume";
import { RenderPlayground } from "./RenderPlayground";

vi.mock("../../components/pdf/pdfjs", () => ({ loadPdf: vi.fn() }));

const loadPdfMock = vi.mocked(loadPdf);
const FIRST_BULLET = "Cut nightly batch";

function pdfDocument(): PdfDocument {
  return {
    pageCount: 1,
    renderPage: vi.fn().mockResolvedValue({ width: 796, height: 1030 }),
    destroy: vi.fn(),
  };
}

function rendered(pdfHash: string): RenderResponse {
  return {
    tex_hash: "tex",
    pdf_hash: pdfHash,
    page_count: 1,
    last_page_fill: 0.5,
    text_map: {
      summary: [{ page: 0, rect: [72, 60, 400, 72] }],
      [FIRST_BULLET_ID]: [{ page: 0, rect: [72, 100, 300, 112] }],
    },
  };
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubRenderApi(...replies: Response[]) {
  const fetchMock = vi.fn();
  for (const reply of replies) fetchMock.mockReturnValueOnce(Promise.resolve(reply));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function postedBody(fetchMock: ReturnType<typeof vi.fn>, call: number): string {
  return String((fetchMock.mock.calls[call]?.[1] as RequestInit | undefined)?.body);
}

beforeEach(() => {
  vi.useFakeTimers();
  loadPdfMock.mockReset();
  loadPdfMock.mockImplementation(() => Promise.resolve(pdfDocument()));
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

test("renders the fixture resume on load and shows the PDF that comes back", async () => {
  const fetchMock = stubRenderApi(json(200, rendered("hash-1")));

  renderWithQuery(<RenderPlayground />);
  await settle();

  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/dev/render");
  expect(postedBody(fetchMock, 0)).toContain("Ada Lovelace");
  expect(loadPdfMock).toHaveBeenCalledWith("/api/v1/files/pdf/hash-1");
});

test("says it is compiling until the first render arrives", () => {
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

  renderWithQuery(<RenderPlayground />);

  expect(screen.getByRole("status").textContent).toBe("Compiling…");
});

test("tells you what to do before anything is selected", async () => {
  stubRenderApi(json(200, rendered("hash-1")));

  renderWithQuery(<RenderPlayground />);
  await settle();

  expect(screen.getByText("Click text in the preview to edit it.")).toBeTruthy();
});

test("clicking a bullet in the preview opens its text for editing", async () => {
  stubRenderApi(json(200, rendered("hash-1")));
  renderWithQuery(<RenderPlayground />);
  await settle();

  fireEvent.click(screen.getByRole("button", { name: new RegExp(`Edit ${FIRST_BULLET}`) }));

  const editor = screen.getByRole<HTMLTextAreaElement>("textbox", { name: "Selected text" });
  expect(editor.value).toMatch(/^Cut nightly batch time/);
});

test("typing recompiles once, after the pause, and the old preview stays until then", async () => {
  const fetchMock = stubRenderApi(json(200, rendered("hash-1")), json(200, rendered("hash-2")));
  renderWithQuery(<RenderPlayground />);
  await settle();
  fireEvent.click(screen.getByRole("button", { name: new RegExp(`Edit ${FIRST_BULLET}`) }));
  const editor = screen.getByRole("textbox", { name: "Selected text" });

  fireEvent.change(editor, { target: { value: "Shipped it" } });
  await settle(200);
  fireEvent.change(editor, { target: { value: "Shipped it fast" } });
  await settle(300);

  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: /Edit Shipped it fast/ })).toBeTruthy();

  await settle(200);

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(postedBody(fetchMock, 1)).toContain("Shipped it fast");
  expect(loadPdfMock).toHaveBeenLastCalledWith("/api/v1/files/pdf/hash-2");
});

test("a compile error is shown and the previous preview is kept", async () => {
  const failure = {
    error: { code: "compile_failed", message: "The resume did not compile.", details: null },
  };
  stubRenderApi(json(200, rendered("hash-1")), json(422, failure));
  renderWithQuery(<RenderPlayground />);
  await settle();
  fireEvent.click(screen.getByRole("button", { name: new RegExp(`Edit ${FIRST_BULLET}`) }));

  fireEvent.change(screen.getByRole("textbox", { name: "Selected text" }), {
    target: { value: "Oops" },
  });
  await settle(500);

  expect(screen.getByRole("alert").textContent).toContain("The resume did not compile.");
  expect(screen.getByRole("button", { name: /Edit Oops/ })).toBeTruthy();
});

test("shows which PDF is on screen", async () => {
  stubRenderApi(json(200, rendered("abcdef0123456789")));

  renderWithQuery(<RenderPlayground />);
  await settle();

  expect(screen.getByText(/abcdef012345/)).toBeTruthy();
});

test("moves focus to the editor when a line is selected", async () => {
  stubRenderApi(json(200, rendered("hash-1")));
  renderWithQuery(<RenderPlayground />);
  await settle();

  fireEvent.click(screen.getByRole("button", { name: new RegExp(`Edit ${FIRST_BULLET}`) }));

  expect(document.activeElement).toBe(screen.getByRole("textbox", { name: "Selected text" }));
});

function recordDownloads(): string[] {
  const saved: string[] = [];
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    saved.push(this.getAttribute("href") ?? "");
  });
  return saved;
}

function downloadButton() {
  return screen.getByRole<HTMLButtonElement>("button", { name: "Download PDF" });
}

function selectFirstBullet() {
  fireEvent.click(screen.getByRole("button", { name: new RegExp(`Edit ${FIRST_BULLET}`) }));
}

function type(text: string) {
  fireEvent.change(screen.getByRole("textbox", { name: "Selected text" }), {
    target: { value: text },
  });
}

describe("download", () => {
  test("offers the PDF that is on screen", async () => {
    const saved = recordDownloads();
    stubRenderApi(json(200, rendered("hash-1")));
    renderWithQuery(<RenderPlayground />);
    await settle();

    fireEvent.click(downloadButton());

    expect(saved).toEqual(["/api/v1/files/pdf/hash-1"]);
  });

  test("is disabled as soon as you type and downloads the new PDF once it is shown", async () => {
    const saved = recordDownloads();
    stubRenderApi(json(200, rendered("hash-1")), json(200, rendered("hash-2")));
    renderWithQuery(<RenderPlayground />);
    await settle();
    selectFirstBullet();

    type("Shipped it");

    expect(downloadButton().disabled).toBe(true);
    expect(screen.getByText("Waiting for the preview to catch up")).toBeTruthy();

    await settle(500);
    expect(downloadButton().disabled).toBe(false);
    fireEvent.click(downloadButton());

    expect(saved).toEqual(["/api/v1/files/pdf/hash-2"]);
  });

  test("stays disabled while the new PDF is still loading, then offers it", async () => {
    const saved = recordDownloads();
    let finish: (document: PdfDocument) => void = () => {};
    loadPdfMock
      .mockImplementationOnce(() => Promise.resolve(pdfDocument()))
      .mockImplementationOnce(() => new Promise<PdfDocument>((resolve) => (finish = resolve)));
    stubRenderApi(json(200, rendered("hash-1")), json(200, rendered("hash-2")));
    renderWithQuery(<RenderPlayground />);
    await settle();
    selectFirstBullet();

    type("Shipped it");
    await settle(500);

    expect(downloadButton().disabled).toBe(true);
    fireEvent.click(downloadButton());
    expect(saved).toEqual([]);

    await act(async () => finish(pdfDocument()));
    await settle();

    expect(downloadButton().disabled).toBe(false);
    fireEvent.click(downloadButton());
    expect(saved).toEqual(["/api/v1/files/pdf/hash-2"]);
  });

  test("is disabled after a failed compile, and says why", async () => {
    const saved = recordDownloads();
    const failure = {
      error: { code: "compile_failed", message: "The resume did not compile.", details: null },
    };
    stubRenderApi(json(200, rendered("hash-1")), json(422, failure));
    renderWithQuery(<RenderPlayground />);
    await settle();
    selectFirstBullet();

    type("Oops");
    await settle(500);
    fireEvent.click(downloadButton());

    expect(downloadButton().disabled).toBe(true);
    expect(screen.getByText("The latest edit did not compile")).toBeTruthy();
    expect(saved).toEqual([]);
  });
});
