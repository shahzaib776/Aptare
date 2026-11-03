import { useQuery } from "@tanstack/react-query";

import { apiGet } from "./client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet("/api/v1/health"),
    retry: false,
    refetchInterval: 30_000,
  });
}
