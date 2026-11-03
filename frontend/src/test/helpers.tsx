import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render } from "@testing-library/react";
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

// With fake timers: lets timers, request promises and the re-renders they cause all finish.
export async function settle(ms = 0) {
  await act(() => vi.advanceTimersByTimeAsync(ms));
  await act(() => vi.advanceTimersByTimeAsync(0));
}
