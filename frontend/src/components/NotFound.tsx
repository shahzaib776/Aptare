import { Link } from "react-router";

export function NotFound() {
  return (
    <section>
      <h1 className="text-xl font-semibold">Page not found</h1>
      <p className="mt-2 text-sm text-slate-600">Nothing lives at this address.</p>
      <Link to="/dev/render" className="mt-4 inline-block text-sm text-blue-700 underline">
        Go to the render playground
      </Link>
    </section>
  );
}
