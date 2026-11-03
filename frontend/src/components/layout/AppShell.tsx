import { Outlet } from "react-router";

import { Sidebar } from "./Sidebar";

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col text-slate-900 md:flex-row">
      <Sidebar />
      <main className="min-w-0 flex-1 p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  );
}
