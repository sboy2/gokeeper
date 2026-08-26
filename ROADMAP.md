# Roadmap

v1 is the scope in [gokeeper-architecture.md](./gokeeper-architecture.md) and the [README](./README.md) non-goals. This file tracks ideas for **after** that baseline ships.

Near-term work (what you plan to build soon) lives in [GitHub Issues](https://github.com/sboy2/gokeeper/issues). Move a roadmap item into an issue when you are ready to start it.

## After v1

- **Family coverage page** — show missing stages in an evolution line via an aggregate query over species × family, not via the matching engine. Architecture already rules out bending this into duplicate rules (§6).
- **Playwright keyboard-flow tests** — optional browser suite for true tab-order / rapid-entry flows. Default CI remains FastAPI `TestClient` (§11.2).
- **Multi-account UI** — schema can leave room; v1 UI is single-account. A later surface could switch profiles without becoming multi-tenant or networked.
- **Screenshot / OCR ingestion** — out of v1; revisit only if offline, local OCR stays dependency-light and does not become the primary entry path.
- **Richer seed / mirror ops** — README guidance for verifying replacement Game Master / Masterfile mirrors when upstreams go stale (§13).
- **Seed SQLite database** — add a seed database that is built from the csv files to copy into the user database to add seed data FK enforcements.
- **Shared local-app contract package** — extract path resolution (`platformdirs` + env/config overrides), `user_version` migrations, `ReferenceTableSpec` (SEED/USER, merge, deactivate), and `FieldSpec` / matching primitives into a small reusable library. Sibling tools share conventions, not gokeeper's Pokémon/postcard tables; combine later as separate SQLite files (or schemas) behind one FastAPI process.

## Not on the roadmap

These stay non-goals unless the product intent changes (see [README](./README.md#non-goals)):

- IV/CP calculators, PvP rank tables, or power-up recommendations
- Niantic sync or any cloud multi-user service
- Spreadsheet-first workflow replacing manual entry

## How to use this file

1. Add a bullet when an idea is real but not soon.
2. Open a GitHub Issue (and optionally link it here) when work is imminent.
3. Delete or move bullets that you abandon so the list stays honest.
