import { useHealth } from "../../api/health";

export function ApiStatus() {
  const { data, isPending, isError } = useHealth();
  const text = isPending
    ? "Checking API…"
    : isError
      ? "API down"
      : `API ok · compiler ${data.compiler}`;

  return (
    <p role="status" className="text-xs text-slate-600">
      {text}
    </p>
  );
}
