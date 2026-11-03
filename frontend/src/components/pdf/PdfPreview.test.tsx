import { act, fireEvent, render, screen } from "@testing-library/react";

import type { TextMap } from "../../api/types";
import { PdfPreview } from "./PdfPreview";
import { loadPdf, type PdfDocument } from "./pdfjs";

vi.mock("./pdfjs", () => ({ loadPdf: vi.fn() }));

const loadPdfMock = vi.mocked(loadPdf);

function fakeDocument(pageCount = 2) {
  const document: PdfDocument = {
    pageCount,
    renderPage: vi.fn().mockResolvedValue({ width: 796, height: 1030 }),
    destroy: vi.fn(),
  };
  return document;
}

const textMap: TextMap = {
  first: [{ page: 0, rect: [72, 100, 300, 112] }],
  second: [{ page: 1, rect: [72, 100, 300, 112] }],
};

function preview(props: Partial<React.ComponentProps<typeof PdfPreview>> = {}) {
  return (
    <PdfPreview
      pdfHash="hash-one"
      textMap={textMap}
      compiling={false}
      onSelect={() => {}}
      describe={(id) => id}
      {...props}
    />
  );
}

async function flush() {
  await act(async () => {});
}

beforeEach(() => {
  loadPdfMock.mockReset();
});

test("loads the PDF stored under the hash it is given", async () => {
  loadPdfMock.mockResolvedValue(fakeDocument());

  render(preview());
  await flush();

  expect(loadPdfMock).toHaveBeenCalledWith("/api/v1/files/pdf/hash-one");
});

test("draws every page to its own canvas at the scale", async () => {
  const document = fakeDocument(2);
  loadPdfMock.mockResolvedValue(document);

  const { container } = render(preview({ scale: 1.3 }));
  await flush();

  const canvases = container.querySelectorAll("canvas");
  expect(canvases).toHaveLength(2);
  expect(document.renderPage).toHaveBeenCalledWith(0, canvases[0], 1.3, expect.any(AbortSignal));
  expect(document.renderPage).toHaveBeenCalledWith(1, canvases[1], 1.3, expect.any(AbortSignal));
});

test("puts each element's click boxes on its own page", async () => {
  loadPdfMock.mockResolvedValue(fakeDocument(2));

  const { container } = render(preview());
  await flush();

  expect(container.querySelector('[data-page="0"] button')?.getAttribute("aria-label")).toBe(
    "Edit first",
  );
  expect(container.querySelector('[data-page="1"] button')?.getAttribute("aria-label")).toBe(
    "Edit second",
  );
});

test("clicking a box reports the element", async () => {
  loadPdfMock.mockResolvedValue(fakeDocument());
  const onSelect = vi.fn();

  render(preview({ onSelect }));
  await flush();
  fireEvent.click(screen.getByRole("button", { name: "Edit second" }));

  expect(onSelect).toHaveBeenCalledWith("second");
});

test("says it is compiling before the first PDF has arrived", () => {
  loadPdfMock.mockReturnValue(new Promise(() => {}));

  render(preview({ compiling: true }));

  expect(screen.getByRole("status").textContent).toBe("Compiling…");
});

test("shows a compiling badge over the pages that are already there", async () => {
  loadPdfMock.mockResolvedValue(fakeDocument());

  const { container, rerender } = render(preview());
  await flush();
  rerender(preview({ compiling: true }));

  expect(screen.getByRole("status").textContent).toBe("Compiling…");
  expect(container.querySelectorAll("canvas")).toHaveLength(2);
  expect(container.firstElementChild?.getAttribute("aria-busy")).toBe("true");
});

test("keeps the old pages and boxes until the new PDF has loaded, then swaps them", async () => {
  const first = fakeDocument(2);
  const second = fakeDocument(1);
  let finish: (document: PdfDocument) => void = () => {};
  loadPdfMock
    .mockResolvedValueOnce(first)
    .mockReturnValueOnce(new Promise<PdfDocument>((resolve) => (finish = resolve)));

  const { container, rerender } = render(preview());
  await flush();
  rerender(preview({ pdfHash: "hash-two", textMap: { third: [{ page: 0, rect: [1, 2, 3, 4] }] } }));
  await flush();

  expect(container.querySelectorAll("canvas")).toHaveLength(2);
  expect(screen.queryByRole("button", { name: "Edit first" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Edit third" })).toBeNull();

  await act(async () => finish(second));

  expect(container.querySelectorAll("canvas")).toHaveLength(1);
  expect(screen.queryByRole("button", { name: "Edit third" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Edit first" })).toBeNull();
  expect(first.destroy).toHaveBeenCalled();
  expect(second.destroy).not.toHaveBeenCalled();
});

test("stops drawing a page when the preview goes away", async () => {
  const document = fakeDocument(1);
  loadPdfMock.mockResolvedValue(document);

  const { unmount } = render(preview());
  await flush();
  const signal = vi.mocked(document.renderPage).mock.calls[0]?.[3];

  expect(signal?.aborted).toBe(false);
  unmount();

  expect(signal?.aborted).toBe(true);
});

test("says so when the PDF cannot be loaded", async () => {
  loadPdfMock.mockRejectedValue(new Error("network"));

  render(preview());
  await flush();

  expect(screen.getByText("The preview could not be loaded.")).toBeTruthy();
});

test("says it is loading while the PDF is being fetched", () => {
  loadPdfMock.mockReturnValue(new Promise(() => {}));

  render(preview());

  expect(screen.getByText("Loading preview…")).toBeTruthy();
});

test("stops saying it is loading once the pages are there", async () => {
  loadPdfMock.mockResolvedValue(fakeDocument());

  render(preview());
  await flush();

  expect(screen.queryByText("Loading preview…")).toBeNull();
});
