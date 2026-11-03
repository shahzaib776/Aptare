// The only file that imports pdf.js. It needs a real canvas, which tests do not have, so tests
// replace this module and everything else stays plain, checkable code.
import * as pdfjs from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

export interface PdfDocument {
  pageCount: number;
  /**
   * Draws page `index` (from 0) into `canvas` and returns the page's size in CSS pixels.
   * Aborting `signal` cancels the drawing: pdf.js refuses a second draw on a canvas that is
   * still being drawn, which is what React's double-run of effects would otherwise cause.
   */
  renderPage(
    index: number,
    canvas: HTMLCanvasElement,
    scale: number,
    signal: AbortSignal,
  ): Promise<{ width: number; height: number }>;
  destroy(): void;
}

export async function loadPdf(url: string): Promise<PdfDocument> {
  const task = pdfjs.getDocument({ url });
  const document = await task.promise;
  return {
    pageCount: document.numPages,
    async renderPage(index, canvas, scale, signal) {
      const page = await document.getPage(index + 1);
      const css = page.getViewport({ scale });
      const size = { width: css.width, height: css.height };
      if (signal.aborted) return size;
      // Draw at the screen's pixel density so text stays sharp, but size the canvas in CSS pixels
      // so the click boxes (which are CSS pixels) line up with it.
      const sharp = page.getViewport({ scale: scale * (window.devicePixelRatio || 1) });
      canvas.width = Math.floor(sharp.width);
      canvas.height = Math.floor(sharp.height);
      canvas.style.width = `${css.width}px`;
      canvas.style.height = `${css.height}px`;
      const drawing = page.render({ canvas, viewport: sharp });
      signal.addEventListener("abort", () => drawing.cancel(), { once: true });
      try {
        await drawing.promise;
      } catch (error) {
        if (!(error instanceof pdfjs.RenderingCancelledException)) throw error;
      }
      return size;
    },
    destroy() {
      void task.destroy();
    },
  };
}
