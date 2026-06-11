# MSFS-GTFS Documentation

A small web app for viewing **Maine State Ferry Service** schedules (Bass Harbor ⇄ Swan's
Island) from a hand-authored GTFS feed. It's a single Flask application that renders its
pages server-side with Jinja templates and uses HTMX for live updates.

> These docs are plain Markdown. They render in **Obsidian** as-is, and the repo also ships
> an `mkdocs.yml` so they can be served as a website later (see [Overview](overview.md)).

## Contents

- **[Overview](overview.md)** — what the app is and does, and how to download, run, and
  deploy it in development and production.
- **[Architecture](architecture.md)** — system topology, what each piece is responsible
  for, and why it's built this way.
- **[Backend](backend.md)** — how the Flask app, GTFS domain model, and schedule logic work.
- **[Frontend](frontend.md)** — how the Jinja templates, HTMX, and CSS design system work.
- **[Code Style](code-style.md)** — the docstring/comment standard used across the code
  (PEP 257 minimal).
