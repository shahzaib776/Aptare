import { useEffect, useRef, useState } from "react";

import type { TextMap } from "../../api/types";
import { ClickRegions } from "./ClickRegions";
import { loadPdf, type PdfDocument } from "./pdfjs";

interface Props {
  pdfHash: string;
  textMap: TextMap;
  /** A new render is being prepared; the pages on screen stay until it is ready. */
  compiling: boolean;
  scale?: number;
  selectedId?: string | undefined;
  onSelect: (id: string) => void;
  describe: (id: string) => string;
  /** Called with the hash of the PDF now on screen: later than `pdfHash` while it loads. */
  onDisplayed?: (pdfHash: string) => void;
}

// A letter page is 612 points wide, so this draws it about 800 CSS pixels wide.
const DEFAULT_SCALE = 1.3;

interface Shown {
  hash: string;
  document: PdfDocument;
  textMap: TextMap;
}

export function PdfPreview({
  pdfHash,
  textMap,
  compiling,
  scale = DEFAULT_SCALE,
  selectedId,
  onSelect,
  describe,
  onDisplayed,
}: Props) {
  // The pages and their boxes are swapped together once the new PDF has loaded, so boxes never
  // sit over a PDF they were not made for.
  const [shown, setShown] = useState<Shown>();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadPdf(`/api/v1/files/pdf/${pdfHash}`).then(
      (document) => {
        if (cancelled) return document.destroy();
        setFailed(false);
        setShown({ hash: pdfHash, document, textMap });
      },
      () => {
        if (!cancelled) setFailed(true);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [pdfHash, textMap]);

  useEffect(() => () => shown?.document.destroy(), [shown?.document]);

  useEffect(() => {
    if (shown) onDisplayed?.(shown.hash);
  }, [shown]);

  return (
    <div aria-busy={compiling} className="relative">
      {compiling && (
        <p
          role="status"
          className="absolute top-2 right-2 z-10 rounded bg-slate-900/80 px-3 py-1 text-xs text-white"
        >
          Compiling…
        </p>
      )}
      {failed && <p className="text-sm text-red-700">The preview could not be loaded.</p>}
      {!shown && !failed && <p className="text-sm text-slate-600">Loading preview…</p>}
      {shown &&
        Array.from({ length: shown.document.pageCount }, (_, index) => (
          <Page key={`${pdfHash}-${index}`} document={shown.document} index={index} scale={scale}>
            <ClickRegions
              page={index}
              scale={scale}
              textMap={shown.textMap}
              selectedId={selectedId}
              onSelect={onSelect}
              describe={describe}
            />
          </Page>
        ))}
    </div>
  );
}

interface PageProps {
  document: PdfDocument;
  index: number;
  scale: number;
  children: React.ReactNode;
}

function Page({ document, index, scale, children }: PageProps) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const drawing = new AbortController();
    if (canvas.current) {
      document.renderPage(index, canvas.current, scale, drawing.signal).catch(() => {
        console.error("Could not draw a page");
      });
    }
    return () => drawing.abort();
  }, [document, index, scale]);

  return (
    <div data-page={index} className="relative mb-4 w-fit bg-white shadow">
      <canvas ref={canvas} className="block" />
      {children}
    </div>
  );
}
