import { fireEvent, render, screen } from "@testing-library/react";

import { DownloadButton } from "./DownloadButton";

interface Saved {
  href: string | null;
  download: string;
}

let saved: Saved[] = [];

beforeEach(() => {
  saved = [];
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    saved.push({ href: this.getAttribute("href"), download: this.download });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("saves the stored file for the hash it is given, as resume.pdf", () => {
  render(<DownloadButton pdfHash="abc123" pending={false} />);

  fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));

  expect(saved).toEqual([{ href: "/api/v1/files/pdf/abc123", download: "resume.pdf" }]);
});

test("a different hash gives a different file", () => {
  render(<DownloadButton pdfHash="zzz999" pending={false} />);

  fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));

  expect(saved[0]?.href).toBe("/api/v1/files/pdf/zzz999");
});

test("is disabled while a compile is pending, and clicking does nothing", () => {
  render(<DownloadButton pdfHash="abc123" pending />);

  const button = screen.getByRole<HTMLButtonElement>("button", { name: "Download PDF" });
  fireEvent.click(button);

  expect(button.disabled).toBe(true);
  expect(saved).toEqual([]);
});

test("is disabled when there is nothing to download yet", () => {
  render(<DownloadButton pdfHash={undefined} pending={false} />);

  const button = screen.getByRole<HTMLButtonElement>("button", { name: "Download PDF" });
  fireEvent.click(button);

  expect(button.disabled).toBe(true);
  expect(saved).toEqual([]);
});

test("leaves no stray link in the page", () => {
  render(<DownloadButton pdfHash="abc123" pending={false} />);

  fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));

  expect(document.querySelector("a[download]")).toBeNull();
});
