# gokeeper

A single-user, locally-run app for tracking a Pokémon GO account: caught Pokémon, medal progress, and the postcard book. On top of inventory, it provides a configurable duplicate detector and a disposition queue (`KEEP` / `REVIEW` / `RELEASE`) so duplicate review is actionable—not just a spreadsheet filter.

**Offline-first.** No Niantic API, no cloud sync. Your data lives in a SQLite file on your machine.

> **Status:** Early development. See [gokeeper-architecture.md](./gokeeper-architecture.md) for the full design. The web UI and domain library are not yet implemented. Post-v1 ideas live in [ROADMAP.md](./ROADMAP.md); near-term work in [GitHub Issues](https://github.com/sboy2/gokeeper/issues).

## Features

- **Pokémon inventory** — IVs, form, costume, moves, origin, background, and more
- **Postcards & medals** — sender, PokéStop, location, tier progress
- **Duplicate detection** — user-defined matching rules, including evolution-family grouping
- **Disposition queue** — review duplicates and mark what to keep or release
- **CSV import/export** — secondary bulk path; manual forms are primary
- **Custom reference data** — add medals, costumes, backgrounds, stickers, PokéStops in-app

## Non-goals

- IV/CP calculators, PvP rank tables, or power-up recommendations
- Living-dex completeness logic
- Screenshot storage or OCR
- Multi-account support or Niantic sync

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended)

## Install

```bash
git clone https://github.com/sboy2/gokeeper.git
cd gokeeper
uv sync
```

## Run

Once the web layer is in place:

```bash
uv run gokeeper
# or
uv run uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The server binds to localhost only—it is not meant to be exposed on a network.

## Where your data lives

Runtime state is stored outside the repository:

| OS | Default location |
|---|---|
| macOS | `~/Library/Application Support/gokeeper/` |
| Linux | `~/.local/share/gokeeper/` |
| Windows | `%LOCALAPPDATA%\gokeeper\` |

Contents:

```
<data_dir>/
├── gokeeper.sqlite
└── backups/
```

**Overrides** (environment wins over config file):

1. **`GOKEEPER_DATA_DIR`** — quick override for tests or a synced folder
2. **`config.toml`** in the platform config dir — persistent override for launcher-started apps

```toml
# ~/.config/gokeeper/config.toml  (Linux example)
data_dir = "~/Documents/gokeeper-data"
```

The resolved path is shown on the Settings page once the UI exists.

## Development

```bash
uv sync --group dev
uv run pytest
```

Tests use `GOKEEPER_DATA_DIR` pointed at a temp directory so they never touch your real database.

### Project layout

```
gokeeper/
├── src/gokeeper/     # domain library (no HTTP, no Jinja)
├── web/              # FastAPI + HTMX + Jinja2 UI
├── scripts/          # seed CSV build pipeline
├── migrations/       # SQLite schema migrations
├── data/seed/        # versioned reference CSVs
└── tests/
```

See [gokeeper-architecture.md](./gokeeper-architecture.md) for services, data model, matching engine, and testing strategy.

### Rebuilding seed data

Reference data ships as committed CSVs under `data/seed/`. To regenerate from upstream sources:

```bash
uv run python scripts/build_seed.py
```

If upstream mirrors change, see §13 in the architecture doc for how to verify replacements.

## Stack

Python · FastAPI · HTMX · Jinja2 · Pico.css · SQLite (stdlib) · platformdirs

HTMX and Pico.css are vendored under `web/static/` so the app works fully offline.

## License

MIT — see [LICENSE](./LICENSE).
