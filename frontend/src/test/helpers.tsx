import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

// A fresh client per test, and no retries, so a failing request shows up immediately.
export function renderWithQuery(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

export function stubHealth(reply: unknown, status = 200) {
  const response = () =>
    new Response(JSON.stringify(reply), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(() => Promise.resolve(response())),
  );
}
