import { fireEvent, render, screen } from "@testing-library/react";

import type { TextMap } from "../../api/types";
import { ClickRegions } from "./ClickRegions";

const textMap: TextMap = {
  b1: [
    { page: 0, rect: [72, 100, 300, 112] },
    { page: 0, rect: [72, 112, 150, 124] },
  ],
  b2: [{ page: 1, rect: [10, 20, 30, 40] }],
  summary: [{ page: 0, rect: [72, 60, 400, 72] }],
};

function regions(props: Partial<React.ComponentProps<typeof ClickRegions>> = {}) {
  return render(
    <ClickRegions
      page={0}
      scale={1.5}
      textMap={textMap}
      onSelect={() => {}}
      describe={(id) => `text of ${id}`}
      {...props}
    />,
  );
}

test("places each box at its PDF rectangle times the scale", () => {
  regions();

  const first = screen.getAllByRole("button", { name: "Edit text of b1" })[0];

  expect(first?.style.left).toBe("108px");
  expect(first?.style.top).toBe("150px");
  expect(first?.style.width).toBe("342px");
  expect(first?.style.height).toBe("18px");
});

test("moves the boxes when the scale changes", () => {
  const { rerender } = regions();

  rerender(
    <ClickRegions
      page={0}
      scale={2}
      textMap={textMap}
      onSelect={() => {}}
      describe={(id) => `text of ${id}`}
    />,
  );

  expect(screen.getAllByRole("button", { name: "Edit text of b1" })[0]?.style.left).toBe("144px");
});

test("shows only the boxes that belong to this page", () => {
  regions({ page: 1 });

  expect(screen.getAllByRole("button")).toHaveLength(1);
  expect(screen.getByRole("button", { name: "Edit text of b2" })).toBeTruthy();
});

test("an element wrapped onto two lines gets two boxes with the same id", () => {
  regions();

  expect(screen.getAllByRole("button", { name: "Edit text of b1" })).toHaveLength(2);
});

test("clicking a box reports the element id", () => {
  const onSelect = vi.fn();
  regions({ onSelect });

  fireEvent.click(screen.getByRole("button", { name: "Edit text of summary" }));

  expect(onSelect).toHaveBeenCalledWith("summary");
});

test("marks the selected element's boxes as pressed and no others", () => {
  regions({ selectedId: "b1" });

  const pressed = screen.getAllByRole("button", { pressed: true });

  expect(pressed).toHaveLength(2);
  expect(screen.getByRole("button", { name: "Edit text of summary", pressed: false })).toBeTruthy();
});
