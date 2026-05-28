## 2026-05-29 — Frontend type system and API client aligned to backend schemas; store moved from positional indexing to player_id lookup

### What was built

**Type-level alignment between frontend and backend API contracts.**

The entire frontend type layer in `frontend/src/types/game.ts` was rewritten from a set of UI-optimised types to exact wire-format types matching the backend's Pydantic schemas in `packages/backend-api/src/backend_api/schemas.py`.

Before this session, the frontend defined types that bore only a passing resemblance to the API: `GameState` had fields like `winner`, `created_at`, `updated_at`, `bag_remaining`, and `time_limit` that the backend never sends (`schemas.py:119-145`, `GameStateOut`). The `PlayerState` type carried a `connected` boolean and an `is_current_player` flag that live nowhere in the backend domain model (`schemas.py:101-116`, `PlayerOut`). The `CreateGameResponse` expected a `session_token` and an embedded `game` object (`schemas.py:148-151`, `CreateGameOut` returns only `code`, `token`, `player_id`). The `JoinGameResponse` expected a `session_token` where the backend returns `token` (`schemas.py:154-157`, `JoinGameOut`). The dictionary enum was `'TWL' | 'CSW21'` but the backend uses `'TWL06' | 'CSW21'` (`models.py:21-23`, `Dictionary`).

The new `game.ts` defines eleven types matching the backend's HTTP boundary verbatim: `TileOut`, `PlacedTileIn`, `PlacedTileOut`, `MoveOut`, `PlayerOut`, `GameStateOut`, `CreateGameRequest`, `CreateGameResponse`, `JoinGameRequest`, `JoinGameResponse`, and a `MoveRequest` discriminated union (`game.ts:78-92`, `PlaceMoveRequest | SwapMoveRequest | PassMoveRequest`). The board grid is typed as `(string | null)[][]` (`game.ts:47`), matching the backend's `Board = list[list[str | None]]` (`models.py:57`).

**API client rewritten to match backend routes.**

`frontend/src/services/api.ts` was rewritten. Five exported functions now call the five backend endpoints exactly:

- `createGame(payload)` — `POST /games`, returns `CreateGameResponse` (`api.ts:37-42`).
- `joinGame(code, payload)` — `POST /games/{code}/join`, returns `JoinGameResponse` (`api.ts:44-49`).
- `fetchGame(code, token)` — `GET /games/{code}` with `Authorization: Bearer <token>`, returns `GameStateOut` (`api.ts:51-55`). Previously this function had no auth parameter; the backend's `GET /games/{code}` requires a session token (`routes/games.py:52-58`, `_require_session` dependency).
- `submitMove(code, payload, token)` — `POST /games/{code}/moves`, returns `GameStateOut` directly (`api.ts:57-63`). Before this session the store expected a `{ game: GameState }` wrapper that does not exist in the backend response.
- `forfeitGame(code, token)` — `POST /games/{code}/forfeit`, returns `GameStateOut` (`api.ts:65-70`).

The generic `request<T>()` helper (`api.ts:12-25`) was kept as-is except that the response body is no longer wrapped — every function returns the JSON-decoded type directly. The `ApiRequestError` class (`api.ts:27-35`) is unchanged.

**Store moved from positional player indexing to player_id UUID lookup.**

`frontend/src/stores/game.ts` was rewritten. Before, `session.value` stored a `player_index: 0 | 1` and the store derived `myPlayer` by indexing into the players array with this integer. This assumption breaks if players ever arrive in a different order, and more immediately it does not match the backend's identity model, where every player is identified by a UUID (`models.py:49-54`, `Player.id`).

The session now stores `player_id: string` (`game.ts:95-99`). The `myPlayer` computed property uses `Array.find()` to match `players[id] === session.player_id` (`game.ts:29-32`). The `opponent` computed property finds the player whose id differs (`game.ts:34-37`). The `isMyTurn` computed property resolves the current player through `players[current_player_index].id` and compares to `session.player_id` (`game.ts:39-43`), rather than comparing positional indices.

The `createGame` method (`game.ts:68-78`) now makes two sequential API calls: first `POST /games` to obtain the game code and auth token, then `GET /games/{code}` (with the token as `Bearer` auth) to retrieve the initial game state. The backend's `CreateGameOut` (`schemas.py:148-151`) deliberately omits the game state — a design decision documented in the backend devlog — so the second hop is necessary. The `joinGame` method (`game.ts:80-85`) needs only one call: the backend's `JoinGameOut` already embeds the full `GameStateOut` in its `state` field (`schemas.py:154-157`).

`fetchGame` was renamed to `fetchGameState` (`game.ts:61-66`) and now requires an established session (the router guard calls it before the SSE stream delivers the initial event).

**Component contract changes.**

*PlayerPanel* (`frontend/src/components/ui/PlayerPanel.vue`): Removed the `PlayerState` dependency. The component now imports `PlayerOut` (`player.ts:3`) and accepts `isActiveTurn: boolean` and `connected: boolean` as separate props (`player.ts:5-10`). The three-state connection dot logic (`player.ts:18-35`) was unchanged but is now driven by explicit props rather than fields embedded in the player data object. The clock display reads `player.time_remaining_secs` (`player.ts:94`) instead of the old `time_remaining`.

*MoveControls* (`frontend/src/components/ui/MoveControls.vue`): Changed from a mix of direct store calls and component emits to a pure event-emitter pattern. The store import was removed. All five button actions — Submit, Clear, Swap/Toggle, Pass, Forfeit — now emit events (`movecontrols.ts:11-17`). The parent `GameView` handles all API calls. Previously the component called `store.submitMove` and `store.forfeit` directly; the `submit` emit was declared but never wired in the template.

*GameBoard* (`frontend/src/components/game/GameBoard.vue`): The `board` prop type changed from `(Tile | null)[][]` (where the old `Tile` had `letter` and `plays_as`) to `(string | null)[][]` (`gameboard.ts:6`). The cell template now renders `board[ri][ci]!.toUpperCase()` (`gameboard.ts:89`) instead of accessing `.letter`. The points subscript span was removed because the backend's `GameStateOut.board` (`schemas.py:123`) contains only letter strings, not tile objects with point values. Blank detection uses a comparison against `' '` (`gameboard.ts:27`) — the backend stores blank tiles as the space character in the bag (`models.py:28`) and as a lowercase letter on the board (`board.py:9`).

*LobbyView* (`frontend/src/views/LobbyView.vue`): The dictionary ref default changed from `'TWL'` to `'TWL06'` (`lobby.ts:12`). The time limit select options were widened to 5, 10, 15, 20, 30 minutes (`lobby.ts:150-157, in template`), replacing the previous 1/3/5/10-minute options on user request. The `CreateGameRequest` payload now sends `time_per_player_secs` (the backend schema name, `schemas.py:29`) rather than `time_limit`.

*GameView* (`frontend/src/views/GameView.vue`): Added `@pass` and `@forfeit` event handlers on `<MoveControls>` (`gameview.ts:64-79, in template`) that call `store.submitMove` with `{ type: 'pass' }` and `store.forfeit` respectively. The winner computation was changed from reading `store.game.winner` (a field that does not exist in `GameStateOut`) to sorting players by score descending (`gameview.ts:47-50`). The board ref is explicitly typed as `(string | null)[][]` (`gameview.ts:36`).

**Swap payload bug fix in usePendingMove.**

`buildSwapPayload` was not receiving the rack array (`frontend/src/composables/usePendingMove.ts:36-38`). Before the fix it mapped each swap index to `''` (empty string). The backend's `SwapMoveRequest` expects `letters: list[str]` containing the actual letter values (`schemas.py:49-51`). The function now accepts `rack: TileOut[]` and resolves letters through `rack[i]?.letter ?? ''` (`pendingmove.ts:36-38`). The caller `buildMovePayload` already passes `rack` for the placement path; the fix extended it to the swap path as well (`pendingmove.ts:45`).

**Router guard session check.**

`frontend/src/router/guards.ts` was updated to check for an existing session before attempting `fetchGameState` (`guards.ts:13-16`). It now handles 401 responses with a dedicated toast message (`guards.ts:24-25`). Previously the guard called `store.fetchGame` (the old name, without auth) and would have received an unhandled 401 from the backend's `_require_session` dependency (`routes/games.py:24-32`).

### Decisions taken

**Decision 1: Frontend types mirror backend schemas exactly, with no translation layer.**

The alternative was to keep the old frontend types and write adapter functions that mapped between the two shapes during API calls. Adapters were rejected because they would need to be maintained in lockstep with the backend and would hide schema mismatches until runtime. Direct mirroring means a `tsc` error during compilation is the first signal of a contract break, not a 422 at runtime. The trade-off is that the frontend types are slightly less ergonomic for UI code — for example, `time_remaining_secs` is a Python-derived name that does not follow JavaScript camelCase conventions. This was accepted as the lesser cost.

**Decision 2: player_id UUID lookup, not positional indexing.**

The previous approach (store `player_index: 0 | 1`, index into `players[]`) assumed the lobby player is always player 0 and the joiner is always player 1. This was inherited from the prototype. The alternative of keeping positional indexing but normalising at the component level was rejected because it masks the backend's identity model and would break if the player insertion order ever changed or if more than two players were supported. Using the UUID returned by the backend as the session anchor (`stores/game.ts:29-37`) means any reordering in the `players` list is transparent to the UI.

**Decision 3: MoveControls emits events instead of calling the store directly.**

The previous component architecture was inconsistent: `handleSubmit` in `MoveControls` called `store.submitMove()` directly, while the `@submit` emit was declared but never wired in the template. `handleForfeit` called `store.forfeit()` directly. The parent `GameView` duplicated some of this logic in its own `handleSubmit` handler. The component was changed to emit five named events (`submit`, `clear`, `pass`, `forfeit`, `toggleSwap`) and the parent handles all API interaction (`MoveControls.vue:11-17`). This makes the component testable without a store mock and keeps the API dispatch logic in one place (`GameView.vue:55-79`).

**Decision 4: Create game makes a second GET request for initial state.**

`POST /games` (`routes/games.py:35-41`) returns only `{code, token, player_id}` (`schemas.py:148-151`), not the full game state. The alternative was to modify the backend to include the state in the create response. This was rejected to avoid editing the backend in the same session as the frontend alignment — the backend's `CreateGameOut` is intentionally minimal, and changing it would require updating tests. The frontend instead calls `GET /games/{code}` with the freshly-returned token (`stores/game.ts:75`). The latency cost of one additional round-trip on game creation is negligible.

### Problems identified

**Problem 1: buildSwapPayload sent empty strings instead of rack letters.**

`buildSwapPayload()` at `frontend/src/composables/usePendingMove.ts:36` mapped each swap index to `''`. When the frontend submitted a `SwapMoveRequest` (`schemas.py:49-51`), the backend received `{"type":"swap","letters":["","",""]}` instead of actual letter values like `["A","R","N"]`.

*Location:* `frontend/src/composables/usePendingMove.ts:36-38`.

*Resolution:* The function now accepts `rack: TileOut[]` and resolves `rack[i]?.letter ?? ''` for each swap index. The caller `buildMovePayload` at line 44 already had `rack` available from its own parameter. *Resolved.* The fix is at line 36-38.

**Problem 2: fetchGame (now fetchGameState) had no auth and would be rejected by the backend.**

The old `store.fetchGame(code)` called `apiFetchGame(code)` which sent `GET /games/{code}` without an `Authorization` header. The backend's `get_game` route at `routes/games.py:52-58` uses `Depends(_require_session)` (`routes/games.py:24-32`), which reads the `Authorization: Bearer <token>` header and returns 401 if absent or invalid.

*Location:* `frontend/src/stores/game.ts:61-66` (new), `frontend/src/services/api.ts:51-55` (new), `routes/games.py:24-32` (unchanged backend).

*Resolution:* The frontend `fetchGame` now accepts a `token` argument and passes it as `Authorization: Bearer <token>` in the request headers. The store's `createGame` method stores the session and immediately calls `apiFetchGame(res.code, res.token)` to retrieve the initial state. The router guard (`guards.ts:19`) calls the renamed `fetchGameState` only after confirming a session exists. *Resolved.*

**Problem 3: GameView computed `winner` from a non-existent field.**

`store.game.winner` was referenced in `GameView.vue:47-49` (old line numbers). The backend's `GameStateOut` (`schemas.py:119-145`) has no `winner` field — the winner is determined by score comparison at the client.

*Location:* `frontend/src/views/GameView.vue:47-50` (current line numbers).

*Resolution:* Replaced with a computed property that sorts `game.players` by `score` descending and takes the first entry. *Resolved.*

**Problem 4: No session check in router guard before API call.**

The router guard (`guards.ts`) called `store.fetchGame` (the old name) unconditionally. If a user navigated directly to `/game/:code` without having created or joined a game, the store had no session token and the API call would fail with 401.

*Location:* `frontend/src/router/guards.ts:13-16`.

*Resolution:* Added an explicit `if (!store.session)` check that redirects to the lobby with a toast message. The `fetchGameState` method now throws if no session exists (`stores/game.ts:62`). *Resolved.*

**Problem 5: GameBoard displayed board tiles from old Tile interface, not string cells.**

The previous `board` prop was typed as `(Tile | null)[][]` where `Tile` had `.letter` and `.plays_as` fields. The backend's `GameStateOut.board` is `list[list[str | None]]` (`schemas.py:123`) — a grid of letter strings. The component template accessed `board[ri][ci]!.letter` and `board[ri][ci]!.plays_as`, both of which would be `undefined` on a string value.

*Location:* `frontend/src/components/game/GameBoard.vue:6,89` (current line numbers).

*Resolution:* The prop type was changed to `(string | null)[][]` and the template renders `board[ri][ci]!.toUpperCase()`. The `.plays_as` span for points was removed. *Resolved.*

### Current state of the codebase

**`frontend/` — structurally complete, pending Redis-backed backend for live testing.**

- `types/game.ts`: 112 lines, 11 export interfaces and 4 export type aliases, all matched to backend schemas.
- `services/api.ts`: 70 lines, 5 exported API functions, all authenticated where required.
- `stores/game.ts`: 147 lines, full Pinia store with UUID-based player identification, SSE lifecycle, and toast management.
- `composables/usePendingMove.ts`: 165 lines, placement/swap ghost logic, payload builders now produce correct wire formats.
- `composables/sse.ts`: 47 lines, unchanged from the two previous sessions.
- `router/guards.ts`: 32 lines, session-validating navigation guard for `/game/:code`.
- `components/game/GameBoard.vue`: 277 lines, board accepts `(string | null)[][]` grid.
- `components/game/TileRack.vue`: 135 lines, unchanged except type import renamed.
- `components/ui/PlayerPanel.vue`: 105 lines, driven by `isActiveTurn` and `connected` props instead of embedded fields.
- `components/ui/MoveControls.vue`: 124 lines, pure event-emitter, no store dependency.
- `components/ui/ToastFooter.vue`: 31 lines, unchanged.
- `views/GameView.vue`: 247 lines, winner computed by score sort, handles pass/forfeit events.
- `views/LobbyView.vue`: 246 lines, `TWL06`/`CSW21` dictionary, 5–30 min time limits.
- `views/PrototypeUI.vue`: ~890 lines, retained from the Artisan migration session, still uses CSS custom properties.

**`packages/backend-api/` — unchanged from the previous session.**

All five HTTP routes and the SSE endpoint are implemented and tested (48 tests). Requires a running Redis instance to serve requests.

**`packages/game-engine/` — unchanged.**

Full game logic (bag, board, scoring, dictionary) with 59 tests.

### Open questions

No unresolved questions from this session.

### References

| File | Key locations |
|---|---|
| `frontend/src/types/game.ts` | `GameStateOut` (L43–53), `MoveRequest` discriminated union (L78–92), `PlayerOut` (L31–37), `PlayerSession` (L95–99) |
| `frontend/src/services/api.ts` | `request<T>()` (L12–25), `createGame` (L37–42), `fetchGame` (L51–55), `submitMove` (L57–63), `forfeitGame` (L65–70) |
| `frontend/src/stores/game.ts` | `myPlayer`/`opponent` computed (L29–37), `isMyTurn` (L39–43), `createGame` (L68–78), `joinGame` (L80–85), `fetchGameState` (L61–66) |
| `frontend/src/composables/usePendingMove.ts` | `buildPlacePayload` (L20–34), `buildSwapPayload` (L36–38), `buildMovePayload` (L40–48) |
| `frontend/src/components/ui/PlayerPanel.vue` | `dotState` computed (L18–35), `formatTime` (L12–16), new `isActiveTurn`/`connected` props (L5–10) |
| `frontend/src/components/ui/MoveControls.vue` | Event emits (L11–17), `handleSubmit` (L21–25), no store import |
| `frontend/src/components/game/GameBoard.vue` | `board: (string \| null)[][]` prop (L6), cell display (L89), blank detection (L27) |
| `frontend/src/views/GameView.vue` | `winner` computed (L47–50), `handlePass`/`handleForfeit` (L68–79) |
| `frontend/src/views/LobbyView.vue` | Dictionary `'TWL06'` default (L12), time-limit options (template L150–157) |
| `frontend/src/router/guards.ts` | Session check (L13–16), 401 handling (L24–25) |
| `packages/backend-api/src/backend_api/schemas.py` | `GameStateOut` (L119–145), `PlayerOut` (L101–116), `CreateGameOut` (L148–151), `JoinGameOut` (L154–157), `MoveRequest` discriminated union (L44–61) |
| `packages/backend-api/src/backend_api/routes/games.py` | `_require_session` (L24–32), all 5 endpoints (L35–81) |
| `packages/game-engine/src/game_engine/models.py` | `GamePhase` enum (L7–11), `Dictionary` enum (L21–23), `Board` type alias (L57), `Player` dataclass (L48–54) |
