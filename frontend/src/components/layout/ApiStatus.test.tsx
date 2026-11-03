import { screen } from "@testing-library/react";

import { renderWithQuery, stubHealth } from "../../test/helpers";
import { ApiStatus } from "./ApiStatus";

afterEach(() => {
  vi.unstubAllGlobals();
});

test("says the compiler is ok when the API reports it", async () => {
  stubHealth({ status: "ok", compiler: "ok" });

  renderWithQuery(<ApiStatus />);

  expect(await screen.findByText("API ok · compiler ok")).toBeTruthy();
});

test("says the compiler is unreachable when the API reports that", async () => {
  stubHealth({ status: "ok", compiler: "unreachable" });

  renderWithQuery(<ApiStatus />);

  expect(await screen.findByText("API ok · compiler unreachable")).toBeTruthy();
});

test("says the API is down when the request fails", async () => {
  stubHealth({ error: { code: "internal_error", message: "boom", details: null } }, 500);

  renderWithQuery(<ApiStatus />);

  expect(await screen.findByText("API down")).toBeTruthy();
});

test("says it is checking before the first answer", () => {
  stubHealth({ status: "ok", compiler: "ok" });

  renderWithQuery(<ApiStatus />);

  expect(screen.getByText("Checking API…")).toBeTruthy();
});
