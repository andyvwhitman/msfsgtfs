import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ScheduleGrid } from "./components/schedule.tsx";
import { Test } from "./components/test.tsx";

createRoot(document.getElementById("schedule")!).render(
  <StrictMode>
    <ScheduleGrid />
  </StrictMode>,
);
