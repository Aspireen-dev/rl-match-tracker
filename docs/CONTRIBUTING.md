# Contributing & code conventions — RL Match Tracker

*Technical document, in English (code and technical docs are in English).*

## General principles

1. **Iterate, don't over-engineer.** Each increment must be small, shippable, and teach something. YAGNI applies everywhere.
2. **Readability over cleverness.** This is a learning project: prefer the boring, explicit solution.
3. **Commit early, commit often.** Small commits with clear messages beat giant "wip" dumps.

## C# / Backend conventions

- .NET 10, C# 14. File-scoped namespaces, nullable reference types enabled (`<Nullable>enable</Nullable>`).
- Naming: `PascalCase` for public members/types, `camelCase` for parameters, `_camelCase` for private fields.
- Prefer explicit types over `var` for local variables (readability); `var` remains mandatory for anonymous types.
- Async all the way: no `.Result`/`.Wait()`, use `async`/`await` with `CancellationToken` where relevant.
- One class per file, organized by feature folders rather than by type folders:
  - `Ingestion/` (socket client, parsers, DTOs)
  - `Domain/` (entities)
  - `Data/` (DbContext, configurations, migrations)
  - `Endpoints/` (minimal API route groups)
- DTOs for API responses; entities never leak to the frontend.
- Errors: explicit result handling in ingestion (log and continue on bad payloads), standard ASP.NET problem details for API errors.

### Structure & naming (the "what changes together?" test)

- Folders are named after **stable concerns** (`Ingestion`, `Domain`,
  `Data`, `Endpoints`), never after a technology that may change (no
  `Socket/`, no `Sqlite/`). A file belongs where its changes happen:
  if the game's stream schema changes, only `Ingestion/` moves; if our
  API contract changes, only `Endpoints/` moves.
- `Domain/` references nothing. Everything references `Domain`.
- **DTOs live at the boundary they describe**: stream DTOs mirror the
  game's JSON vocabulary (they never reference `Domain`) in
  `Ingestion/Dtos/`, and the parser translates them to entities; API
  DTOs project from `Domain` in `Endpoints/`. A change in the external
  schema stops at the boundary; only a business field change crosses
  layers, and it should.
- Queries live in the endpoint handlers (LINQ against the `DbContext`);
  `Data/` provides the vocabulary, not the queries.
- Frontend: a component lives in `features/<name>`; it is promoted to
  shared `components/` only once several features use it (promotion
  earned through usage, never predicted — YAGNI).

## TypeScript / Frontend conventions

- TypeScript **strict mode**; no `any` (use `unknown` + type guards when needed).
- Functional components + hooks only. No classes.
- TanStack Query for all server state; no ad-hoc `useEffect` fetching.
- Components organized by feature (`features/dashboard`, `features/matches`), shared primitives in `components/`.
- Naming: `PascalCase` components/files, `camelCase` variables, `SCREAMING_SNAKE_CASE` constants.
- Styling: Tailwind utility classes; extract shared patterns only when repeated 3+ times.

## Commits

Conventional Commits, in English:

```
feat(api): parse UpdateState tick and persist match summary
fix(web): fix win rate rounding on dashboard
docs: add architecture decision records
```

## Testing strategy (introduced progressively — see ROADMAP)

- **First test assets**: capture real JSON payloads from the game and store them as fixtures. The parser is the most valuable thing to test.
- Backend: xUnit. Test parsing (fixtures), aggregation logic (pure functions), and API endpoints with `WebApplicationFactory`.
- Frontend: Vitest + React Testing Library. Test rendering of key components with mocked API data.
- Testing timeline is decided by the ROADMAP, not by feel: iterations 0-4 ship without tests (build the thing first); iteration 5 retrofits the test suite on stable code (parser fixtures, aggregation functions, endpoints, key components); **from iteration 5 onward, every new increment ships with its own tests** — no new untested feature lands after that point.

### Fixture privacy

Real captures may contain third-party players' display names and platform IDs. Fixtures committed to the public repository are anonymized: display names replaced with generated placeholders, platform UIDs replaced with fake values, **preserving the exact field formats** (`Platform|Uid|Splitscreen`). Raw, non-anonymized captures stay on the developer machine: `captures/` ignores everything (`captures/*`) **except the capture tooling** (`!captures/*.py` — scripts are code and are committed; `*.jsonl` raw data never is). The anonymization script lives in `tests/anonymize_fixture.py` (committed fixtures go to `tests/Api.Tests/Fixtures/`) and is the only sanctioned path from a raw capture to a committed fixture: `python tests/anonymize_fixture.py captures/<raw>.jsonl tests/Api.Tests/Fixtures/<name>.jsonl`. Anonymization works on two levels: known field names (`Name`, `PlayerName`, `PrimaryId`, `MatchGuid`, case-insensitive) **and patterns** (any string shaped like `Platform|uid|Splitscreen` or a 32-hex GUID is anonymized whatever its field name, so a new field added by the game cannot leak an identifier). Third-party data is used for realistic testing only, never exposed.

**Privacy guard-rail**: `tests/check_fixtures_privacy.py` scans fixtures for real personal data (non-placeholder names, real-looking platform UIDs/GUIDs) and fails on any hit. The ID formats live in `tests/stream_ids.py`, shared by both scripts, as a **per-platform spec** (`PLATFORM_SPECS`: exact uid regex per platform — Steam `^7656119\d{10}$`, Epic 32 hex, PS4 18-19 digits, XboxOne 16 digits — plus a fake-uid factory preserving each platform's shape) with predicates on top (`parse_primary_id`, `is_primary_id`, `is_guid`, `is_fake_primary_id`, `is_fake_guid`). Unknown future platforms fall back to a generic rule (hex ≥ 16 chars or numeric ≥ 15 digits). It runs automatically on every commit via the pre-commit hook in `.githooks/` — activate it once per clone with `git config core.hooksPath .githooks`. You can also run it manually: `python tests/check_fixtures_privacy.py [file.jsonl ...]` (no argument = all of `tests/Api.Tests/Fixtures/`).

**Logging rule**: player names and platform IDs are personal data. In the backend they are only ever logged at `Debug` level (active in Development only); production logs (`Information` and up) never contain a player name or ID. `StreamEventParser` also caps payload size and truncates invalid-JSON previews so a malformed payload cannot dump personal data into the logs.

## Definition of Done (per increment)

- Feature works manually (checked against a real or fixture payload).
- Code reviewed with the assistant (see mentoring rules): transformations applied by the author, naming and structure cleaned up; every notion introduced can be explained by the author in 2-3 sentences.
- No `Console.WriteLine` debug leftovers; use `ILogger`.
- Documentation touched if architecture/decisions changed.
- Commit(s) follow the convention above.

## CI (introduced in V2)

GitHub Actions on push/PR: `dotnet build`, `dotnet test`, frontend `lint` + `tsc --noEmit` + `vitest run`. Later: a release workflow publishing the app locally (self-contained publish).

## Things we deliberately do NOT do (yet)

- No Docker (until PostgreSQL in V2).
- No authentication (local app).
- No CI/CD complexity beyond lint/test.
- No microservices, no message broker, no Redis. One process. It's a local tool.
