import { useState } from "react";

import { useRender } from "../../api/render";
import type { TailoredResume } from "../../api/types";
import { DownloadButton } from "../../components/pdf/DownloadButton";
import { PdfPreview } from "../../components/pdf/PdfPreview";
import { fixtureResume } from "./fixtureResume";
import { textOf, withText } from "./resumeText";

const DESCRIPTION_LENGTH = 50;

function describe(resume: TailoredResume, id: string): string {
  const text = textOf(resume, id) ?? id;
  return text.length > DESCRIPTION_LENGTH ? `${text.slice(0, DESCRIPTION_LENGTH)}…` : text;
}

/** Developer page: edit a fixture resume by clicking it, and watch it recompile. */
export function RenderPlayground() {
  const [resume, setResume] = useState(fixtureResume);
  const [selectedId, setSelectedId] = useState<string>();
  const { render, isCompiling, isPending, error } = useRender(resume);
  // The preview keeps the old PDF on screen until the new one has loaded; Download must offer
  // the one on screen (EX-2), so it uses the hash the preview reports, not the newest render.
  const [displayedHash, setDisplayedHash] = useState<string>();

  // EX-3: no download while what is on screen is about to change, or no longer matches the text.
  const note =
    isPending || (render && render.pdf_hash !== displayedHash)
      ? "Waiting for the preview to catch up"
      : error
        ? "The latest edit did not compile"
        : undefined;

  return (
    <section>
      <h1 className="text-xl font-semibold">Render playground</h1>
      {error && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {error.message}
        </p>
      )}
      <div className="mt-4 flex flex-col gap-6 lg:flex-row">
        <div className="min-w-0 overflow-x-auto">
          {render ? (
            <>
              <div className="mb-2 flex flex-wrap items-center gap-3">
                <DownloadButton pdfHash={displayedHash} pending={note !== undefined} />
                <p className="text-xs text-slate-600">
                  Showing PDF {(displayedHash ?? render.pdf_hash).slice(0, 12)}…
                </p>
                {note && <p className="text-xs text-slate-600">{note}</p>}
              </div>
              <PdfPreview
                pdfHash={render.pdf_hash}
                textMap={render.text_map}
                compiling={isCompiling}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onDisplayed={setDisplayedHash}
                describe={(id) => describe(resume, id)}
              />
            </>
          ) : (
            !error && (
              <p role="status" className="text-sm text-slate-600">
                Compiling…
              </p>
            )
          )}
        </div>
        <div className="lg:w-96 lg:shrink-0">
          {selectedId ? (
            <label className="flex flex-col gap-2 text-sm font-medium">
              Selected text
              <textarea
                // A new element per selection, so focus moves to the editor each time.
                key={selectedId}
                autoFocus
                rows={6}
                value={textOf(resume, selectedId) ?? ""}
                onChange={(event) => setResume(withText(resume, selectedId, event.target.value))}
                className="rounded border border-slate-300 p-2 font-normal"
              />
            </label>
          ) : (
            <p className="text-sm text-slate-600">Click text in the preview to edit it.</p>
          )}
        </div>
      </div>
    </section>
  );
}
