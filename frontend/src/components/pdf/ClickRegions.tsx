import type { TextMap } from "../../api/types";

interface Props {
  page: number;
  /** CSS pixels per PDF point: the same scale the page was drawn at. */
  scale: number;
  textMap: TextMap;
  selectedId?: string | undefined;
  onSelect: (id: string) => void;
  /** Short text for screen readers, so each box says what it edits. */
  describe: (id: string) => string;
}

/** Transparent buttons laid over the text of one page; the PDF itself is never touched (ED-3). */
export function ClickRegions({ page, scale, textMap, selectedId, onSelect, describe }: Props) {
  return (
    <>
      {Object.entries(textMap).flatMap(([id, placements]) =>
        placements
          .filter((placement) => placement.page === page)
          .map((placement, index) => {
            const [x0, y0, x1, y1] = placement.rect;
            const selected = id === selectedId;
            return (
              <button
                key={`${id}-${index}`}
                type="button"
                aria-label={`Edit ${describe(id)}`}
                aria-pressed={selected}
                onClick={() => onSelect(id)}
                className={`absolute cursor-pointer rounded-sm hover:bg-blue-500/10 focus-visible:outline-2 focus-visible:outline-blue-600 ${selected ? "bg-blue-500/10 outline-2 outline-blue-600" : ""}`}
                style={{
                  left: x0 * scale,
                  top: y0 * scale,
                  width: (x1 - x0) * scale,
                  height: (y1 - y0) * scale,
                }}
              />
            );
          }),
      )}
    </>
  );
}
