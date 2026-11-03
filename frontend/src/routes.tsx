import { Navigate, type RouteObject } from "react-router";

import { AppShell } from "./components/layout/AppShell";
import { NotFound } from "./components/NotFound";
import { RenderPlayground } from "./features/dev/RenderPlayground";

export const routes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dev/render" replace /> },
      { path: "dev/render", element: <RenderPlayground /> },
      { path: "*", element: <NotFound /> },
    ],
  },
];
