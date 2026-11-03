import { useState } from "react";

import { useRender } from "../../api/render";
import type { TailoredResume } from "../../api/types";
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
  const { render, isCompiling, error } = useRender(resume);

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
              <p className="mb-2 text-xs text-slate-600">
                Showing PDF {render.pdf_hash.slice(0, 12)}…
              </p>
              <PdfPreview
                pdfHash={render.pdf_hash}
                textMap={render.text_map}
                compiling={isCompiling}
                selectedId={selectedId}
                onSelect={setSelectedId}
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
