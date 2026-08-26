# Contributing to gokeeper

Thanks for your interest in gokeeper. This document covers how to work on the repository. For product context and design, see [gokeeper-architecture.md](./gokeeper-architecture.md). For install and run instructions, see [README.md](./README.md).

## Scope

gokeeper is a single-user, offline-first local app for Pokémon GO inventory and duplicate review. Before opening a PR, check the non-goals in the [README](./README.md#non-goals) and [architecture doc §1.3](./gokeeper-architecture.md#13-non-goals). Features outside that scope (IV calculators, Niantic sync, multi-account UI, OCR, and similar) are unlikely to be accepted.

## Getting started



### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)



### Setup

```bash
git clone https://github.com/sboy2/gokeeper.git
cd gokeeper
uv sync --group dev
```

Run the full test suite before opening a PR:

```bash
uv run pytest
```

Run a subset while iterating:

```bash
uv run pytest tests/unit
uv run pytest tests/web
uv run pytest tests/unit/test_matching.py -k "null"
```



### Local data directory

**Never run tests against your real database.** Test fixtures set `GOKEEPER_DATA_DIR` to a temporary directory automatically. When running the app manually during development, point it at a throwaway directory:

```bash
export GOKEEPER_DATA_DIR=/tmp/gokeeper-dev
uv run gokeeper
```

See [README § Where your data lives](./README.md#where-your-data-lives) and [architecture §7.1](./gokeeper-architecture.md#71-database-location) for override behavior.

## Workflow

1. **Discuss non-trivial changes first** — open a [GitHub issue](https://github.com/sboy2/gokeeper/issues) for new features or design questions.
2. **Branch from** `main` — use a short descriptive name (`feature/postcard-filters`, `fix/import-validation`).
3. **Make focused changes** — one concern per PR when possible.
4. **Add or update tests** — see [Testing](#testing) below.
5. **Open a pull request** — describe what changed, why, and how you verified it.



### Pull request checklist

- [ ] `uv run pytest` passes (includes the 100% coverage gate)
- [ ] New behavior has tests (or a brief note in the PR explaining why not)
- [ ] Schema changes include a migration under `migrations/`
- [ ] Seed/reference changes go through `scripts/build_seed.py` with updated CSVs in `data/seed/`
- [ ] Architecture-affecting changes update [gokeeper-architecture.md](./gokeeper-architecture.md)



## Project structure

```
gokeeper/
├── src/gokeeper/     # domain library — no HTTP, no Jinja
├── web/              # FastAPI + HTMX + Jinja2 UI
├── scripts/          # seed CSV build pipeline
├── migrations/       # SQLite schema migrations
├── data/seed/        # versioned reference CSVs (committed public API)
└── tests/{unit,web}/
```

Full layout and service inventory: [architecture §10](./gokeeper-architecture.md#10-project-layout) and [§2.2](./gokeeper-architecture.md#22-service-inventory).

## Layer boundaries

These rules keep the codebase testable and reusable. Violating them in a PR will be flagged in review.


| Layer        | Location                 | May do                                          | Must not do                                     |
| ------------ | ------------------------ | ----------------------------------------------- | ----------------------------------------------- |
| Web          | `web/`                   | Parse requests, render templates, call services | SQL, direct `matching/` imports, business logic |
| Services     | `src/gokeeper/services/` | Transactions, orchestration                     | Render HTML                                     |
| Repositories | `src/gokeeper/db/`       | SQL, return dicts                               | Business logic, open/commit transactions        |
| Matching     | `src/gokeeper/matching/` | Pure signature computation                      | Database access, I/O of any kind                |
| Registry     | `src/gokeeper/registry/` | Declare `FieldSpec` metadata                    | HTTP or template imports                        |


`src/gokeeper/` must not import from `web/`.

## Code conventions



### Python style

- **Type hints** on all function signatures (parameters and return types).
- **NumPy-style docstrings** on public functions, methods, and classes.
- **Explicit naming** — prefer `annualized_return` over `ret`, `pipeline_run_id` over `run_id`.
- **Small, focused functions** — one clear responsibility per function.
- **No ORM** — hand-written SQL in repositories only.



### Adding a tracked attribute

1. Add a database migration in `migrations/`.
2. Add a `FieldSpec` in the appropriate registry module.
3. Update repositories and services as needed.
4. Add tests for coercion, matching (if `matchable=True`), and any import/export paths.

See [architecture §2.1](./gokeeper-architecture.md#21-the-field-registry).

### Schema migrations

Migrations are linear SQL files applied via `user_version`. Do not introduce Alembic or an ORM migration tool. Test migrations against an in-memory database with `foreign_keys=ON`. See [architecture §11.1](./gokeeper-architecture.md#111-pure-core).

### Seed data

- **Runtime contract:** committed CSVs under `data/seed/`.
- **Build pipeline:** `scripts/build_seed.py` reads pinned upstream fixtures and emits those CSVs.
- **Do not** import upstream JSON directly from application code.

Regenerate seed CSVs after changing the build script or source adapters:

```bash
uv run python scripts/build_seed.py
```

If an upstream mirror changes, see [architecture §13](./gokeeper-architecture.md#13-open-items) for verification guidance.

## Testing

Testing strategy is documented in [architecture §11](./gokeeper-architecture.md#11-testing). Summary of expectations:


| Area            | Expectation                                               |
| --------------- | --------------------------------------------------------- |
| `matching/`     | Property and table-driven tests; pure functions only      |
| `migrations/`   | Apply full chain on `:memory:`; assert final schema       |
| `services/`     | Transaction behavior, merge/seed invariants               |
| `importer/`     | Golden CSV fixtures; error collection; idempotency        |
| `build_seed.py` | Golden fixtures; hard fail on unmatched joins             |
| `web/`          | `TestClient` smoke, form round-trips, HTMX fragment swaps |


### Coverage

`uv run pytest` measures line and branch coverage for `src/gokeeper` and `web`, and fails if either falls below 100%. Configuration lives in `pyproject.toml` (`pytest-cov` / `[tool.coverage.*]`). Do not lower `fail_under` to land a PR — add tests, or justify a narrow exclusion in the PR description.

Browser automation (Playwright) is optional and not required for most web changes.

## Commit messages

Use imperative mood and keep the subject line under ~72 characters:

```
Add postcard disposition filter to list view
Fix import validation for unknown reference values
```



## Reporting bugs and requesting features

Use [GitHub Issues](https://github.com/sboy2/gokeeper/issues). Include:

- OS and Python version
- Steps to reproduce (or the feature you want and why)
- Expected vs actual behavior
- For data issues: whether the problem is in seed data or user-entered data



## License

By contributing, you agree that your contributions are licensed under the [MIT License](./LICENSE).