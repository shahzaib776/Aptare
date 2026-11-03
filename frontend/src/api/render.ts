import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { apiPost } from "./client";
import type { RenderResponse, TailoredResume } from "./types";

// ED-2: recompile about 500 ms after the last change.
const RENDER_DELAY_MS = 500;
const TEMPLATE_ID = "dense-single";

export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

/**
 * Compiles the resume a moment after it stops changing.
 *
 * `render` is the last successful compile, so the previous page stays on screen while the next
 * one compiles and when it fails (ED-2). `isPending` also covers the wait before a compile
 * starts, because until then the preview does not show what was just typed.
 */
export function useRender(resume: TailoredResume) {
  const settled = useDebouncedValue(resume, RENDER_DELAY_MS);
  const query = useQuery({
    queryKey: ["render", settled],
    queryFn: () => apiPost("/api/v1/dev/render", { resume: settled, template_id: TEMPLATE_ID }),
    retry: false,
    // The same resume always compiles to the same PDF, so a repeat never needs a new request.
    staleTime: Infinity,
  });

  const [render, setRender] = useState<RenderResponse | undefined>();
  if (query.data && query.data !== render) setRender(query.data);

  return {
    render,
    isCompiling: query.isFetching,
    isPending: settled !== resume || query.isFetching,
    error: query.error,
  };
}
