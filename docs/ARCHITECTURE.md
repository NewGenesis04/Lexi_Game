# NEO Scrabble — Architecture & Decisions

## Overview

A modern, low-latency online Scrabble game. Monorepo with two packages: `game-engine` (pure, zero-dependency domain logic) and `backend-api` (FastAPI modular monolith). SSE for server-to-client pushes, HTTP POST for client actions. Dockerized on a single VPS.

---
### Static System Architecture & Infrastructure
                          ┌────────────────────────────────────────────────────────┐
                          │                   Client (Web SPA)                     │
                          │      EventSource (SSE) ◄───┐       │                   │
                          └────────────────────────────┼───────┼───────────────────┘
                                                        │       │ POST /moves (HTTP)
                                                        │       ▼
                          ┌────────────────────────────┼───────────────────────────┐
                          │               Docker Container (FastAPI)               │
                          │                                                        │
                          │   routes/  ──►  services/  ──►  repositories/          │
                          │                                      │                 │
                          │   ┌────────────────────────┐         │                 │
                          │   │  game-engine (Package) │         │                 │
                          │   │  ───────────────────── │         │                 │
                          │   │  • board | scoring     │         │                 │
                          │   │  • bag | logic         │         │                 │
                          │   │  • Pickled Frozenset   │         │                 │
                          │   │    (Loaded in RAM)     │         │                 │
                          │   └────────────────────────┘         │                 │
                          │                                      │                 │
                          │   ┌────────────────────────┐         │                 │
                          │   │ In-Process SSE Manager │◄────────┤                 │
                          │   │  • dict[code, Lock]    │         │                 │
                          │   └────────────────────────┘         │                 │
                          └──────────────────────────────────────┼─────────────────┘
                                                                  │ Read / Write TCP
                                                                  ▼
                          ┌────────────────────────────────────────────────────────┐
                          │               Docker Container (Redis)                 │
                          │   • game:{code}       ──► GameState JSON               │
                          │   • session:{token}   ──► PlayerSession JSON           │
                          │   • active_games      ──► Set[code]                    │
                          └────────────────────────────────────────────────────────┘



## Sequential Data Flow
                Client            Route           Service          Engine           Repo          SSE / Timer
                  │                 │                │               │               │                 │
                  │── POST /moves ─►│                │               │               │                 │
                  │                 │── handle_move ─►│               │               │                 │
                  │                 │                │──[Acquire Lock]               │                 │
                  │                 │                │─── validate_move ────────────►│                 │
                  │                 │                │◄─── [Returns True] ───────────│                 │
                  │                 │                │─── apply_move ───────────────►│                 │
                  │                 │                │◄─── [New GameState] ──────────│                 │
                  │                 │                │                               │                 │
                  │                 │                │─────── SET game:{code} ──────►│                 │
                  │                 │                │                                                 │── Cancel / Spawn Task
                  │                 │                │────────────────────────────────────────────────►│── Broadcast Sanitized
                  │                 ◄─── Return 200 ─│                                                 │
                  ◄── 200 OK ───────│                │                                                 │



## Disconnect & Adjournment State Machine
                                                ┌───────────────┐
                                                │    CREATED    │
                                                └───────┬───────┘
                                                        │ Player Joins
                                                        ▼
                                                ┌───────────────┐
                                                │    PLAYING    │◄────────────────────────────────┐
                                                └───────┬───────┘                                 │
                                                        │                                         │
                                        Either Player   │ Disconnect                              │ Both Players
                                        Socket Drops    │                                         │ Reconnect
                                                        ▼                                         │
                                                ┌───────────────┐                                 │
                                                │   ADJOURNED   │─────────────────────────────────┘
                                                │  DISCONNECT   │ (Freeze Turn Clock -> Save Remaining Secs)
                                                └───────┬───────┘ (Spawn 5-Min asyncio.Task)
                                                        │
                                                        │ Last Connected Player Drops OR
                                                        │ 5-Min Task Expires / Opponent Left
                                                        ▼
                                                ┌───────────────┐
                                                │    PAUSED     │◄─── (Turn status flag to PAUSED)
                                                └───────┬───────┘
                                                        │
                                                        │ 60-Sec Sweep Task checks:
                                                        │ now() - updated_at > 30 mins
                                                        ▼
                                                ┌───────────────┐
                                                │ GARBAGE WIPE  │ ──► (Evict keys from Redis)
                                                └───────────────┘

Key design bets:
- All validation server-side in game-engine — no challenge mechanics needed
- SSE pushes full GameState — dumb client
- Opaque bearer tokens — upgrade to JWT later
- Per-game asyncio.Lock for mutation safety
- Per-game asyncio.Task for time bank — no polling
- Join-by-6-digit-code with nicknames; accounts added layer later
- Three end conditions: spent time clock out, 6 consecutive passes, or bag empty + tile rack penalt

## Decided Design

### Q1. Tile Set
**Decision:** Standard English (NASPA-style, 100 tiles, 15×15 board).
**Rationale:** Only variant supported at launch. Adding more is additive — tile bag config is data, not code.

### Q2. Word Lists
**Decision:** TWL (North American) and CSW21 (international). Both bundled. Per-game selection.
**Rationale:** User owns CSW21.txt already. Two dictionaries cover the vast majority of demand.

### Q3. Dictionary Loading
**Decision:** Both dictionaries compiled into pickle'd `frozenset`s at build-time, loaded at server startup.
**Rationale:** Correct by construction — no risk of AI-generated DAWG corruption. ~15 MB RAM per dictionary is negligible. See Q15 for full rationale.

### Q4. GameState Structure
**Decision:** Sketch defined; details TBD during implementation. Fields include: board, bag, players, current_player_index, phase, move_history, dictionary, scores, consecutive_passes, last_move.
**Rationale:** No limitation on tile swaps. Core fields only; extend as needed.

### Q5. Game Joining
**Decision:** Invite code — 6-character alphanumeric. Creator shares code out-of-band.
**Rationale:** No lobby system needed. MVP simplicity. Code is generated on creation.

### Q6. Player Identity (Pre-Accounts)
**Decision:** Nickname + invite code. No cookies, no auth ceremony.
**Rationale:** Lightweight. First player creates game with nickname; joiner enters code + nickname. Clean upgrade path to accounts later (add account_id column).

### Q7. Turn Timing
**Decision:** Synchronous with per-player time bank. Match creator sets the time limit.
**Rationale:** Standard tournament rules. "Low-latency" means fast games.

### Q8. SSE Channel Design
**Decision:** Single SSE connection per session (one EventSource). Multiplexed by game_id internally. Full GameState pushed on each event.
**Rationale:** One EventSource is simpler client-side. Full state push eliminates extra round-trip — 5–8 KB is negligible bandwidth.

### Q9. Redis Role
**Decision:** Redis used for game state persistence from day one. SSE subscriptions stay in-process.
**Rationale:** Survives container restarts/deploys without losing games. SSE is in-process because pub/sub adds latency for no benefit with a single worker — clients reconnect after restart and re-subscribe via their session token.

### Q10. HTTP Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/games` | Create game |
| POST | `/games/{code}/join` | Join game |
| POST | `/games/{code}/moves` | Submit move (place/swap/pass) |
| POST | `/games/{code}/forfeit` | Resign |
| GET | `/games/{code}` | Fetch GameState |
| GET | `/events?token=<session>` | SSE stream |

6-pass game-end detected server-side automatically.

### Q11. Monorepo Layout
**Decision:** uv workspace with two packages.
```
neo-scrabble/
├── pyproject.toml              # root workspace
├── packages/
│   ├── game-engine/
│   │   ├── pyproject.toml
│   │   └── src/game_engine/
│   │       ├── models.py       # GameState, Tile, Move
│   │       ├── board.py        # Grid logic, placement validation
│   │       ├── scoring.py      # Score calc, premium squares
│   │       ├── bag.py          # Tile bag, draw, exchange
│   │       ├── dawg.py         # DAWG loader/checker
│   │       ├── dictionaries/   # Compiled .dawg files
│   │       └── scripts/
│   │           └── build_dawg.py
│   └── backend-api/
│       ├── pyproject.toml
│       └── src/backend_api/
│           ├── main.py
│           ├── routes/
│           │   ├── games.py
│           │   └── events.py
│           ├── services/
│           │   └── game_service.py
│           ├── repositories/
│           │   └── game_repo.py
│           ├── game_manager.py
│           ├── sse_manager.py
│           └── session.py
```

### Q12. Layers & Dependency Flow
**Decision:** Routes → Services → Repositories → In-Memory Store. Services import `game-engine` directly (no port/adapter layer).
**Rationale:** You control both sides of the boundary. The engine exposes pure functions on plain data classes — testability is free.

### Q13. Concurrency
**Decision:** `dict[str, asyncio.Lock]` — one lock per game. Acquired on all mutating endpoints. Reads skip the lock.
**Rationale:** Per-game isolation with zero contention between games. No deadlock risk.

### Q14. Session Tokens
**Decision:** Server-generated opaque bearer token (SHA256 hex prefix). Stored in `dict[str, PlayerSession]`. Passed as `?token=` query param for SSE.
**Rationale:** Simple, stateless-ish (session state on server). No JWT complexity at launch. Upgrade path: swap to JWT later.

### Q15. Dictionary Format
**Decision:** Build-time script compiles lexicon into a pickle'd `frozenset`. Loaded at server startup via `pickle.load()`.
**Rationale:** Correct by construction. O(1) lookup, ~15 MB RAM — negligible. No risk of AI-generated DAWG corruption. Serves as test oracle for a future migration to `pytries`/DAWG library if prefix queries become needed.

### Q16. Testing Strategy
**Decision:** Three layers — unit tests for engine (pytest, 95% coverage); unit tests for API routes (httpx AsyncClient, mocked services); integration tests (full HTTP, real in-memory repo). Property-based tests (hypothesis) deferred to post-MVP.
**Rationale:** Traditional tests cover the core paths. Property-based tests add regression safety for scoring and validation but are overkill initially.

### Q17. Challenge Flow
**Decision:** No challenge mechanic. Engine validates every move server-side before accepting. Invalid moves return HTTP 422.
**Rationale:** Trust the DAWG, not the opponent. Simpler UX. Challenge can be added later if user feedback demands it.

### Q18. Time Bank Enforcement
**Decision:** Per-game `asyncio.Task` that `await sleep(remaining_time)`. Cancelled and re-created on each move. Sub-tasks fire warnings at 50% and 10% remaining.
**Rationale:** No polling, no cron drift. Lightest-weight approach.

### Q19. Frontend
**Decision:** Web SPA (framework TBD).
**Rationale:** SSE is native to browsers. SSE event schema is kept client-agnostic.

### Q20. Deployment
**Decision:** Docker container on a VPS (single box, Dockerfile in backend-api/).
**Rationale:** Reproducible deploys, trivial rollback. Single container handles 50–100 concurrent games on a $5/mo box.

### Q21. Game-End Conditions
**Decision:** Three standard conditions:
- Bag empty + a player empties their rack → end, remaining opponent tiles subtracted from their score, added to emptying player
- 6 consecutive passes → end, scores as-is
- A player's time bank hits zero → auto-forfeit
Ties: returned as-is, no tiebreaker logic.

### Q22. Move Submission Schema
**Decision:** Client sends an explicit list of tile placements:
```json
{
  "type": "place",
  "tiles": [
    {"row": 7, "col": 7, "letter": "S"},
    {"row": 7, "col": 8, "letter": "T"},
    {"row": 7, "col": 9, "letter": "A"},
    {"row": 7, "col": 10, "letter": "R"}
  ]
}
```
Blanks include `"letter": " ", "plays_as": "T"`. Engine validates adjacency, contiguity, and dictionary.
**Rationale:** Explicit, unambiguous. Client already computes pixel positions for board preview.

### Q23. Redis Data Model
**Decision:** Simple key-value with JSON strings (not Hashes). Two key namespaces:
- `game:{code}` → serialized GameState JSON
- `session:{token}` → serialized PlayerSession JSON
`active_games` Set for monitoring/cleanup.
**Rationale:** GameState is always read/written as a whole unit. No benefit from field-level Hashes.

### Q24. SSE Subscription Storage
**Decision:** In-process Python dict, not Redis pub/sub.
**Rationale:** Single-worker deployment. On restart, SSE connections drop; clients reconnect with their session token and re-subscribe. Redis pub/sub would add latency and complexity for zero benefit at this scale.

### Q25. Rack Security — Storage
**Decision:** Racks stored inside the single `game:{code}` GameState JSON (Option A). Opponent racks filtered server-side in a sanitization layer.
**Rationale:** Option B (separate Redis keys) creates data desynchronization bugs. One source of truth.

### Q26. Dual-Channel Sanitization (Anti-Leak)
**Decision:** A `sanitize_game_state(raw, requesting_player_id)` function strips the opponent's rack before data reaches **both** the HTTP response and the SSE broadcast. The SSE manager broadcasts per-recipient (one sanitized payload per player, not one raw broadcast).
**Rationale:** Prevents rack leakage through either channel. If raw GameState is accidentally logged or broadcast, opponent tiles are never in the payload.

### Q27. Disconnect State Machine — 5-Minute Grace Period
**Decision:** Any disconnect (by either player) immediately freezes the active turn clock and triggers a 5-minute grace period. Game enters `PAUSED` state. Both players must reconnect for the game to resume. If 5 minutes elapse without full reconnection, forfeit: if exactly one player is online, they win; if both are offline, the game is garbage-collected as a draw after 30 minutes. On reconnect, the frozen clock resumes from `paused_time_left` (stored in Redis alongside `game:{code}`).
**Rationale:** Simplifies the state machine — no distinction between "current player disconnected" vs "opponent disconnected during your turn." Eliminates clock-race conditions.

### Q28. Double Disconnect
**Decision:** When both players are disconnected, the game remains in `PAUSED` state. A background sweep task checks for paused games older than 30 minutes and garbage-collects them as draws.
**Rationale:** No double-timer conflict. Games can't linger in Redis forever.

### Q29. Disconnect Timer Semantics
**Decision:** Each disconnect event gets a fresh 5-minute timer.
**Rationale:** Simplest to reason about. Prevents "second disconnect has a tighter clock" confusion.

### Q30. Reconnect UX
**Decision:** On SSE re-establish, the server pushes `game_paused` event (if game is still paused) or `game_resumed` (if both players are back) over the fresh connection. No polling — the SSE stream is the source of truth.
**Rationale:** Session token survives as long as the game exists; cleaned up on game end or 30-min sweep.

### Q31. Session Token Lifetime
**Decision:** Session lives as long as the game exists. Cleaned up when the game ends or garbage-collected.
**Rationale:** Tokens are opaque random 32-char hex strings — no security concern from long lifetimes.