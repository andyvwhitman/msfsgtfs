# Code Style — Docstrings & Comments

This project documents Python code with **PEP 257 minimal** docstrings: plain-prose summaries,
no structured field syntax (`Args:`, `:param:`, etc.). It's the lightest standard, reads
cleanly in plain text, and is the official Python baseline. Use this as the convention across
projects.

References: [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/) ·
[PEP 8 — Comments](https://peps.python.org/pep-0008/#comments).

## Rules

1. **Every module, class, and public function/method gets a docstring.** Trivial internal
   one-liners may be self-evident, but prefer a short docstring anyway.
2. **Start with a one-line imperative summary** ("Return…", "Build…", "Zip…"), ending in a
   period, fitting on one line. For returning functions, "Return X" is preferred over
   "Returns X".
3. **Add a body only when it earns its place** — separated from the summary by one blank line.
   Use it for the *why*, edge cases, units/formats, or important caveats. Don't restate the
   signature.
4. **No field syntax.** Describe parameters/returns in prose within the body when they aren't
   obvious. (Type hints, if added later, carry type info — the prose carries intent.)
5. **Triple double-quotes** (`"""`), even for one-liners. Closing `"""` on its own line for
   multi-line docstrings.
6. **Inline `#` comments explain *why*, not *what*.** Keep them for non-obvious mechanics
   (e.g. a pandas filter, a GTFS quirk). If a docstring already covers the reasoning, don't
   duplicate it in a comment.

## Docstring vs. comment

- **Docstring** — the contract/intent of a module, class, or function (its first statement).
  Discoverable via `help()` and tooling.
- **Inline `#` comment** — a local note about a specific line or block of implementation.

## Examples (from this codebase)

One-line summary:

```python
def _format_display_time(t):
    """Format a GTFS "HH:MM:SS" string for display, e.g. "6:45 AM"."""
```

Summary + body (units/intent and a forward-looking caveat, no field syntax):

```python
def _trip_progress_pct(departure_time, arrival_time, now_seconds):
    """Return percent of a voyage elapsed (0-100), clamped.

    A guesstimate from elapsed/expected duration, given the GTFS departure and
    arrival "HH:MM:SS" times and the current seconds-since-midnight. This is a
    stand-in until GPS/AIS data provides a true position-based estimate.
    """
```

Module docstring:

```python
"""Flask configuration, loaded via app.config.from_pyfile.

Defines the environment flag (DEV_MODE), the GTFS feed path, and the route/stop
identifiers and display names for the single supported ferry route.
"""
```

Class docstring:

```python
class Trip():
    """A single GTFS trip: one scheduled sailing with its ordered stop times."""
```

## Templates and CSS

Jinja templates and `style.css` aren't Python, but follow the same spirit: a brief
top-of-file comment stating the file's role — `{# ... #}` in templates, `/* ... */` in CSS.
