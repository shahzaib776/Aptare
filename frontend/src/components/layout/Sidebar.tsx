import { NavLink } from "react-router";

import { ApiStatus } from "./ApiStatus";

// Only pages that exist are listed; each phase adds its own.
const links = [{ to: "/dev/render", label: "Render playground" }];

export function Sidebar() {
  return (
    <aside className="flex shrink-0 flex-col gap-4 border-b border-slate-200 bg-slate-50 p-4 md:w-60 md:gap-6 md:border-r md:border-b-0">
      <div className="text-lg font-semibold">Aptare</div>
      <nav aria-label="Main" className="flex flex-col gap-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex min-h-11 items-center rounded px-3 text-sm ${isActive ? "bg-slate-200 font-medium" : "hover:bg-slate-100"}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="md:mt-auto">
        <ApiStatus />
      </div>
    </aside>
  );
}
