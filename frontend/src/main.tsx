import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ScheduleGrid } from "./components/schedule.tsx";
import { Test } from "./components/test.tsx";

document.addEventListener("DOMContentLoaded", () => {
  const headerDate = document.getElementById("header-date");
  if (headerDate) {
    headerDate.textContent = new Date().toLocaleString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }
});

createRoot(document.getElementById("schedule-container")!).render(
  // <StrictMode>
  <ScheduleGrid />,
  // </StrictMode>,
);
