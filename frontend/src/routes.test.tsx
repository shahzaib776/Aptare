import { fireEvent, screen } from "@testing-library/react";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";

import { routes } from "./routes";
import { renderWithQuery, stubHealth } from "./test/helpers";

beforeEach(() => {
  stubHealth({ status: "ok", compiler: "ok" });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function at(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  renderWithQuery(<RouterProvider router={router} />);
  return router;
}

test("the home page sends you to the render playground", async () => {
  const router = at("/");

  expect(await screen.findByRole("heading", { name: "Render playground" })).toBeTruthy();
  expect(router.state.location.pathname).toBe("/dev/render");
});

test("a page renders inside the app shell with its navigation", async () => {
  at("/dev/render");

  expect(await screen.findByRole("heading", { name: "Render playground" })).toBeTruthy();
  expect(screen.getByRole("navigation", { name: "Main" })).toBeTruthy();
  expect(screen.getByText("Aptare")).toBeTruthy();
});

test("the link to the page you are on is marked as current", async () => {
  at("/dev/render");

  const link = await screen.findByRole("link", { name: "Render playground" });

  expect(link.getAttribute("aria-current")).toBe("page");
});

test("an unknown address shows a not-found page, still inside the shell", async () => {
  at("/nope");

  expect(await screen.findByRole("heading", { name: "Page not found" })).toBeTruthy();
  expect(screen.getByRole("navigation", { name: "Main" })).toBeTruthy();
});

test("the not-found page offers a way back", async () => {
  const router = at("/nope");

  fireEvent.click(await screen.findByRole("link", { name: "Go to the render playground" }));

  expect(await screen.findByRole("heading", { name: "Render playground" })).toBeTruthy();
  expect(router.state.location.pathname).toBe("/dev/render");
});
