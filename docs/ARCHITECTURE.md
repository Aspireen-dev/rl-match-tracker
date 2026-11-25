# Architecture — RL Match Tracker

*Technical documentation, in English. Explains HOW the system works and the rationale behind each decision.*

## High-level data flow

```
Rocket League (PC)                    Backend (ASP.NET Core)               Frontend (React + TS)
      │                                      │                                  │
      │ TCP JSON stream (localhost:49123)     │                                  │
      ├──────────────────────────────────────▶│                                  │
      │  - periodic state ticks (30/s)        │  parse → validate → aggregate   │
      │  - discrete match events             │  persist (EF Core → SQLite)      │
      │                                      │                                  │
      │                                      │── REST API (JSON) ──────────────▶│
      │                                      │◀─ HTTP GET (TanStack Query) ────│
      │                                      │                                  │
      │                                      │◀─(later, V3) SignalR live ─────│
```

The game is the **server** of the TCP socket; our backend is a **client**. The backend is itself the server of the REST API consumed by the frontend. Everything runs on the player's machine. No external network access required.

## Components

### 1. Ingestion service (background worker)

- A `BackgroundService` (IHostedService) maintaining a persistent TCP connection to the game socket.
- Reads newline/delimited JSON messages, deserializes into strongly-typed DTOs matching the official Stats API schema (`UpdateState`, match events...).
- Tolerant by design: the game may restart, the socket may drop → reconnection loop with exponential backoff. Unknown JSON fields must not break the parser.
- Emits parsed events on an in-memory channel/bus consumed by the aggregation layer.

### 2. Aggregation & persistence (EF Core)

Design principle: **store raw match summaries, compute analytics on demand** (for V1 volumes — thousands of rows — no pre-aggregation needed).

Core entities:

- `Match` : MatchGuid, date, arena, playlist/mode, duration, overtime, winner team, final score.
- `Player` : platform (`Steam`/`Epic`/...), platformId, displayName. Unique per (platform, platformId).
- `MatchPlayer` : stats of one player in one match (goals, assists, saves, shots, score, demos, team). Junction with the "own goal" flag if needed.
- `Session` (V2) : grouping of consecutive matches by time gap.
- From iteration 2, each persisted match is stored with its consolidated raw JSON payload (the buffered stream of that match), alongside the parsed aggregates. Raw payloads are kept forever: they are the recalculation and retrocompatibility guarantee.

Notes:
- Some fields are CONDITIONAL in the stream (e.g. `MatchGuid` only in online play) → all parsers must handle missing data without crashing.
- Spectator-only fields (boost, speed) are visible for the local player's team; treat them as "nice to have", never as guaranteed.
- SQLite provider via EF Core, kept **provider-agnostic** (no raw SQL, no SQLite-specific types) so the V2 PostgreSQL switch stays simple (no raw SQL rewrite), while the migration itself remains real work: data transfer utility, tests on both providers. Migrations are EF Core migrations, not hand-written SQL.

### 2.1 Local player identity (blocking decision for aggregation)

The stream has NO "local player" flag: every lobby player arrives with a
`PrimaryId` (`Platform|Uid|Splitscreen`). Resolution strategy (V1):

- The user configures their platform (Steam/Epic) and account ID once in
  app settings; the app builds the expected `PrimaryId` and stores it in
  its settings — NOT as a flag on the `Player` entity. "My stats"
  aggregations join on this configured value.
- First-match validation: the ingestion layer reports whether the
  configured `PrimaryId` appears in the current lobby; the UI shows
  "player identified / not found, check settings" — immediate feedback
  that the setup works. Aggregation starts only once the identity is
  validated.
- Auto-detection heuristics (platform of the running install, "player
  present in every match") are rejected for V1: unverifiable and
  untestable. A first-run wizard (click your name in the first lobby)
  remains a possible later UX improvement — it would only write the
  same configured value.

### 3. REST API (Minimal APIs)

V1 endpoints (indicative):

- `GET /api/matches` — paginated list, filters (mode, date range, result).
- `GET /api/matches/{id}` — match detail with all players.
- `GET /api/stats/overview` — aggregates: total matches, win rate, avg goals/saves/assists, per-mode breakdown.
- `GET /api/health` — from iteration 0: liveness probe returning `{"status":"ok"}`; extended in iteration 3 with the game connection status ("is the game connected?").

Principles: DTOs only (never expose entities directly), explicit response shapes documented for the frontend, versioned under `/api`.

### 4. Frontend (React + TypeScript)

- Vite + React + TypeScript strict.
- TanStack Query for server state (caching, refetching).
- Recharts for charts. Tailwind CSS for styling.
- V1 pages: Dashboard (overview cards + recent matches), Match list, Match detail, Settings (platform + account ID, see § 2.1).

## Key technical decisions (and why)

| Decision | Rationale |
|---|---|
| .NET 10 (LTS) | Modern C#; the point of the project is also to migrate the author's skills from .NET Framework to modern ASP.NET Core. |
| SQLite in V1, PostgreSQL in V2 | Local single-user tool: SQLite is zero-config and plenty for the data volume. The V2 switch is a deliberate learning increment (PostgreSQL, Docker, data migration are core full-stack job skills), not a technical necessity — the app would run on SQLite forever. EF Core kept provider-agnostic keeps the switch simple (no raw SQL), but the migration is still real work: data transfer utility, tests on both providers. |
| BackgroundService + Channel for ingestion | Decouples socket reading from processing; teaches async pipelines. |
| Store raw matches, aggregate on read | Simple, sufficient volume, avoids premature optimization. Revisit only if data grows (V3+). |
| Minimal APIs over controllers | Less boilerplate, modern idiom; learn convention-over-configuration without ceremony. |
| React over Angular | Larger job market, bigger ecosystem; author's priority is employability. |
| SignalR deferred to V3 | Live UI is valuable but not core; V1/V2 prove the data layer first. |
| Tests introduced per-increment (not day 1) | Learning project: first make the thing work, then learn testing on stable ground (fixtures of real JSON captures as first test assets). |
| Health endpoint as a JSON envelope from iteration 0 | The status code is the machine contract (200 = alive); the JSON body (`{"status":"ok"}`) keeps the response human-readable in `curl`/browser and the shape ready for the iteration 3 extension (game connection state) without restructuring. |
| Store raw match payload (JSON) alongside aggregates, from iteration 2 | Enables full recalculation if the parsing logic evolves or a bug is found; adds a compatibility guarantee that aggregate-only storage cannot offer. Cost is negligible (KBs per match). The buffering needed is the same match-boundary detection built in iteration 2 anyway; iteration 1 is deliberately excluded because match boundaries are not yet detected there. |
| Stream parsing via `JsonSerializer.DeserializeAsyncEnumerable<T>(stream, topLevelValues: true)` (iteration 1) | The game emits concatenated top-level JSON objects `{"Event":...,"Data":"..."}` with **no separator** (~3 KB, 30/s). The default `DeserializeAsyncEnumerable` mode expects a JSON array and fails on this stream; `topLevelValues: true` (.NET 9+) reads successive top-level values natively in streaming, including the buffering of incomplete values. A manual `Utf8JsonReader` splitter was built first, then replaced by this one-liner. |
| Stream DTOs in `Ingestion/Dtos/`, parsed in two steps: envelope `StreamEnvelope` then `Data` re-deserialized into the event DTO (iteration 1) | The official doc shows `Data` as a JSON object, but the actual wire format sends it as an **escaped JSON string** (confirmed on real captures) → two deserializations. Unknown JSON fields are ignored by default by System.Text.Json (forward compatibility for free); fields marked CONDITIONAL/SPECTATOR in the doc are nullable in the DTOs. |

## Risks & mitigations

- **Game updates may change the payload** → keep captured raw JSON samples as fixtures; parser designed to ignore unknown fields (forward-compatible).
- **No rank/MMR in the stream** → product decision documented in PRODUCT.md (manual entry later, maybe).
- **Spectator-conditional fields** → never build features that assume these fields exist.
- **Socket availability** → health endpoint + UI indicator ("game connected / waiting for game").
- **Playlist/mode reliability is NOT confirmed** — a comparable project judges the streamed data unreliable for the ranked/casual/extra distinction. To be verified on real fixtures during iteration 1 (play one match of each type). Fallback plan: classify by team size + arena + Rumble pickups (reliable for playlist shapes: 1v1/2v2/3v3, Hoops, Dropshot, Rumble, Snow Day); ranked-vs-casual stays indistinguishable and the product promise becomes "stats per playlist shape", to be documented in PRODUCT.md if confirmed. No user-declared mode in V1: unverifiable declarative data corrupts stats silently.
- **Stats API can silently stop emitting** → per the official doc, `TAStatsAPI.ini` is read **only at game launch**, and `PacketSendRate` (default 0 = disabled) is what enables the API. Observed symptom: port 49123 stays LISTENING but zero packets are sent (client connects, receives nothing). Fix: verify `PacketSendRate`/`Port` under `[TAGame.MatchStatsExporter_TA]` and **restart the game**. (`bEnabled=1` is a legacy UE3 key from old tutorials, not required by the official doc; kept in our ini as harmless — A/B test planned to confirm which of restart vs bEnabled actually restored the stream.)
- **GoalScored is emitted twice per goal** → once with data (`GoalTime`, `Scorer`, `GoalSpeed`), once empty (`GoalTime=0`, empty `Scorer`) during the goal replay. Never count raw `GoalScored` events; count goals via `StatfeedEvent` with `EventName='Goal'` or via `Game.Teams[].Score` / `MatchEnded.WinnerTeamNum`.

## Repository layout (monorepo)

```
/
├── RLMatchTracker.slnx               # .NET solution (XML format — the .NET 10 SDK default)
├── src/
│   ├── Api/                          # ASP.NET Core backend (ingestion + REST)
│   │   ├── Api.csproj                # project identity: target framework, nullable, web SDK
│   │   ├── Program.cs                # entry point: bootstrap + endpoint routes
│   │   ├── appsettings*.json         # external config, layered per environment
│   │   └── Properties/
│   │       └── launchSettings.json   # local run profiles/ports (only used by dotnet run / IDE launch)
│   └── Web/                          # React + TypeScript frontend (Vite)
│       ├── index.html                # the single HTML page; React mounts into #root
│       ├── vite.config.ts            # dev server config (plugins, /api proxy in dev)
│       ├── tsconfig*.json            # TS compiler options (app code vs Vite's own config)
│       ├── package.json              # scripts + dependencies (the .csproj of the front)
│       ├── package-lock.json         # exact pinned dependency versions (committed)
│       ├── public/                   # static files served as-is
│       └── src/                      # React code (main.tsx entry point, App.tsx root component)
├── tests/
│   ├── Api.Tests/      # xUnit (from iteration 5)
│   ├── Web.Tests/      # Vitest + RTL (from iteration 5)
├── docs/               # the .md files (this one, PRODUCT, ROADMAP...)
├── README.md
├── MENTORING.md        # session rules between the author and the assistant
└── .github/workflows/  # CI (introduced in V2)
```
