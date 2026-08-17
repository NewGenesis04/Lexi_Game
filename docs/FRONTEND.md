# NEO Scrabble — Frontend Architecture & Decisions

## Overview

A lightweight Vue 3 Single Page Application (SPA) that renders a "Dumb UI" driven entirely by a single reactive `gameState` object fed from the FastAPI SSE stream. All user actions are HTTP POSTs to the backend — the frontend never mutates game state locally. It displays, it does not decide.

**Stack:** Vue 3.5 + Composition API (`<script setup>`) · TypeScript 6 · Vite 6 · TailwindCSS v4 · Pinia 3 · vue-router 4 · pnpm

No auto-import plugins. All imports are explicit.

---

### Static Architecture

```
                          ┌──────────────────────────────────────┐
                          │           Browser (SPA)              │
                          │                                      │
                          │  App.vue                             │
                          │   ├── <router-view>                  │
                          │   │   ├── LobbyView.vue              │
                          │   │   │   └── Create / Join form     │
                          │   │   └── GameView.vue               │
                          │   │       ├── PlayerPanel (opponent) │
                          │   │       ├── GameBoard (15×15)      │
                          │   │       ├── TileRack               │
                          │   │       ├── MoveControls           │
                          │   │       └── PlayerPanel (self)     │
                          │   └── ToastFooter                    │
                          │                                      │
                          │  Pinia (useGameStore)                │
                          │   ├── gameState ◄── updateLocalState │
                          │   ├── session (token + player_index) │
                          │   └── toasts                         │
                          │                                      │
                          │  composables/sse.ts                  │
                          │   └── EventSource (idempotent)       │
                          │                                      │
                          │  services/api.ts                     │
                          │   └── fetch() wrapper                │
                          └──────┬───────────────────────────────┘
                                 │ GET /events?token=    (SSE)
                                 │ POST /games/*         (HTTP)
                                 ▼
                          ┌──────────────────────────────────────┐
                          │         FastAPI Backend               │
                          └──────────────────────────────────────┘
```

---

### Data Flow

```
LobbyView                          GameView
   │                                  │
   │──createGame()/joinGame()──►api   │──submitMove()/forfeit()──►api
   │◄──GameState ◄──updateLocalState  │◄──GameState ◄──updateLocalState
   │──router.push(/game/:code)        │
                                      │
                                      │  SSE Stream (connectSSE)
                                      │◄──GameState ◄──updateLocalState
                                      │
                                   re-render
                                   (Vue Reactivity)
```

---

### Route Guard Flow (`/game/:code`)

```
beforeEnter (gameGuard)
  │
  ├── store.disconnectSSE()          // kill any stale connection
  ├── store.fetchGame(code)          // GET /games/{code}
  │     ├── success ──► connectSSE() // open fresh EventSource
  │     └── 404 ──────► addToast() + store.reset() + redirect /
  └── enter route
```

---

## Directory Structure

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
└── src/
    ├── main.ts                      # createApp, Pinia, Router
    ├── App.vue                      # <router-view> + ToastFooter
    ├── style.css                    # @import "tailwindcss"
    ├── router/
    │   ├── index.ts                 # createRouter (/ + /game/:code)
    │   └── guards.ts                # gameGuard — 404 → toast → redirect
    ├── stores/
    │   └── game.ts                  # useGameStore (single source of truth)
    ├── composables/
    │   └── sse.ts                   # EventSource lifecycle (idempotent)
    ├── services/
    │   └── api.ts                   # HTTP client (create/join/move/forfeit/fetch)
    ├── types/
    │   └── game.ts                  # GameState, MovePayload, PlayerSession, etc.
    ├── views/
    │   ├── LobbyView.vue            # Create / Join tabbed form, avatar picker
    │   ├── GameView.vue             # Board composition root, overlay orchestration
    │   └── RulesView.vue            # Static rules page (opens in new tab)
    ├── constants/
    │   ├── avatars.ts                # AVATARS map (10 bundled PNGs) + AVATAR_KEYS
    │   └── board.ts                  # Premium-square layout, board dimensions
    └── components/
        ├── game/
        │   ├── GameBoard.vue        # 15×15 grid, ghost-tile placement, blank-letter picker
        │   └── TileRack.vue         # Current player's tiles, selection/swap highlighting
        └── ui/
            ├── PlayerPanel.vue          # Desktop side panel: score, clock, connected status
            ├── PlayerMini.vue           # Mobile header-strip equivalent of PlayerPanel
            ├── MoveControls.vue         # Submit/Clear/Swap/Pass/Forfeit, sticky on mobile
            ├── BoardBanner.vue          # Turn/status banner above the board
            ├── GameOverCard.vue         # Win/loss/tie overlay, dismissible + reopenable
            ├── GamePausedCard.vue       # Disconnect overlay while phase is 'paused'
            ├── LeaveConfirmCard.vue     # Confirm-before-forfeit modal for the Leave button
            ├── MoveHistorySidebar.vue   # Slide-in full move log
            └── ToastFooter.vue          # Fixed-bottom error/info/success/warning toasts
```

---

## Decided Design

### FQ1. Framework & Build Tooling
**Decision:** Vue 3.5 with Composition API (`<script setup>`), Vite 6, TypeScript 6, pnpm.
**Rationale:** Vue's reactivity maps naturally to full-state SSE pushes. Vite provides instant HMR. Explicit imports keep the codebase predictable for contributors.

### FQ2. CSS Strategy
**Decision:** TailwindCSS v4 via `@tailwindcss/vite` plugin. CSS-first `@theme` configuration, no `tailwind.config.js`.
**Rationale:** v4's Rust compiler is fast, and CSS-first `@theme` removes a config file. Utility classes keep component files self-contained.

### FQ3. State Management
**Decision:** Pinia store (`useGameStore`) as the single source of truth. No component-local game state.
- `game` — `ref<GameState | null>`
- `session` — `ref<PlayerSession | null>`
- `toasts` — `ref<ToastMessage[]>`
- `connected` — `ref<boolean>` (SSE status)

Computed getters: `phase`, `isMyTurn`, `myPlayerIndex`, `myPlayer`, `opponent`.
**Rationale:** Pinia provides devtools integration, modularity, and cross-component access without prop threading.

### FQ4. Single Mutation Entry Point
**Decision:** Every incoming GameState payload — whether from `fetchGame` (HTTP), `gameGuard` (route check), or SSE push — must go through one function: `updateLocalState(payload: GameState)`.
**Rationale:** Prevents duplicate parsing logic. Gives a single choke-point for logging, sanitization, or devtools hooking.

### FQ5. SSE Connection Lifecycle
**Decision:** Split responsibility:
- **Store** (`game.ts`) exposes `connectSSEStream()` and `disconnectSSE()` semantic actions.
- **Composable** (`sse.ts`) manages raw `EventSource` mechanics: open, close, auto-reconnect, JSON parse.

`sse.ts` is strictly idempotent — before creating a new `EventSource`, it closes and nullifies any existing instance. Prevents zombie stream leaks on rapid navigation.
**Rationale:** Transport logic stays testable in isolation. The store owns the contract; the composable owns the socket.

### FQ6. Router & Route Guards
**Decision:** `vue-router` with three routes:
| Path | View | Guard | Purpose |
|------|------|-------|---------|
| `/` | `LobbyView` | None | Create or join a game |
| `/game/:code` | `GameView` | `gameGuard` | Active game board |
| `/rules` | `RulesView` | None | Static rules reference, opened in a new tab from the in-game header |

`gameGuard` (`router/guards.ts`):
1. Tears down any existing SSE connection
2. Redirects to `/` immediately (with a toast) if there's no local session at all
3. Calls `store.fetchGameState(code)`
4. On success — opens SSE stream, enters route
5. On 404/401/other — pushes a status-specific error toast, calls `store.reset()`, redirects to `/`
**Rationale:** Shareable URLs for multiplayer invite. Guard ensures the game exists before the component mounts.

### FQ7. HTTP Client Layer
**Decision:** Thin `services/api.ts` wrapping `fetch()` with JSON headers, error class (`ApiRequestError`), and typed methods:
- `createGame()` → `POST /games`
- `joinGame()` → `POST /games/{code}/join`
- `submitMove()` → `POST /games/{code}/moves`
- `forfeitGame()` → `POST /games/{code}/forfeit`
- `fetchGame()` → `GET /games/{code}`

Base URL from `VITE_API_BASE` env var, defaults to `localhost:8000`.
**Rationale:** No Axios dependency. The surface is small enough that `fetch` suffices. `ApiRequestError` carries status code for the guard's 404 check.

### FQ8. TypeScript Interfaces
**Decision:** All backend shapes mapped in `types/game.ts` as plain interfaces:
- `GameState` — board, players, phase, move_history, scores, time_bank, etc.
- `PlayerState` — id, nickname, rack, score, time_remaining, connected, is_current_player
- `MovePayload` — type (place/swap/pass), tiles[], letters[]
- `MoveRecord` — logged move with score, words_formed
- `CreateGamePayload` / `CreateGameResponse` / `JoinGamePayload` / `JoinGameResponse`
- `PlayerSession` — token, nickname, player_index
- `ToastMessage` — id, text, type (error/info/success)
- `ApiError` — detail

**Rationale:** TypeScript catches shape mismatches at compile time. The interfaces are the contract between frontend and backend.

### FQ9. Component Architecture (Dumb UI)
**Decision:** Components never call the API directly. They read from the store/composables and emit user gestures; `GameView.vue` is the only place that calls `store.submitMove` / `store.forfeit`.
- `LobbyView` — calls `store.createGame()` / `store.joinGame()`, navigates on success; owns avatar/nickname/dictionary/time-limit selection
- `RulesView` — static content, no store access
- `GameView` — composition root; owns `usePendingMove()` (draft placement/swap state), derives `winner`/`isDraw`/`endReason` from `store.game`, and orchestrates which overlay card is visible
- `GameBoard` — renders the 15×15 grid from `store.game.board` plus the in-progress ghost tiles/blank-letter picker passed down from `usePendingMove()`
- `TileRack` — renders `store.myPlayer.rack`, highlights selected/placed/swap-marked indices
- `PlayerPanel` / `PlayerMini` — desktop side panel and mobile header-strip variants of the same score/clock/connection display; `PlayerMini` is the one shown below `lg:`
- `MoveControls` — Submit / Clear / Swap-toggle / Pass / Forfeit; only rendered when it's the viewer's turn
- `BoardBanner` — turn/status strip above the board
- `GameOverCard` / `GamePausedCard` / `LeaveConfirmCard` — full-screen overlay cards keyed off `store.phase` (`finished` / `paused`) and local `showLeaveConfirm` state; `GameOverCard` is dismissible and reopenable via a header "RESULT" button rather than being locked open
- `MoveHistorySidebar` — slide-in panel over `store.game.move_history`
- `ToastFooter` — renders `store.toasts` array, fixed bottom, auto-dismiss after 5s

Components are organized by domain: `components/game/` (board-surface primitives) and `components/ui/` (chrome, panels, overlays).
**Rationale:** Store-driven rendering makes the UI a pure function of `gameState`. Components are trivially testable.

### FQ10. Toast System
**Decision:** `store.addToast(text, type)` pushes a `ToastMessage` with auto-generated ID and 5-second TTL. `ToastFooter` renders the array fixed at the bottom of the viewport.
**Rationale:** Centralized toast state means route guards, views, and the store all use the same error-reporting path. No ad-hoc alert() or inline error divs.

### FQ11. Tile Placement
**Decision:** Click-then-click, implemented in `composables/usePendingMove.ts` and consumed by `GameView`/`GameBoard`/`TileRack`. Selecting a rack tile then clicking an empty board cell records a local "ghost" (`Map<"row,col", {rackIndex, row, col}>`) — nothing is sent to the server yet. Clicking a ghost removes it and re-selects that rack tile. A separate swap-mode toggle (mutually exclusive with placement) lets the player multi-select rack tiles for exchange instead. Blank tiles get their played-as letter via a picker on the placed ghost, tracked in a `blankLetterMap`. `Submit` (`MoveControls`) converts the draft into the real payload — `{type: 'place', tiles: [{row, col, letter, plays_as}]}` or `{type: 'swap', letters}` — and calls `store.submitMove()`; only success clears the draft, so a rejected move (e.g. `INVALID_WORD`) leaves the attempted layout on the board for the player to adjust.
**Rationale:** Click-then-click is the most intuitive for desktop and doesn't require drag-and-drop plumbing. Keeping the draft entirely local (not synced through the store/SSE) means a half-built word never touches `GameState` — it's the one piece of "pending" UI state that's allowed to live outside the store, precisely because it's never sent until `Submit` and is discarded on any state transition away from `playing` (see the `store.phase` watcher in `GameView.vue`).

### FQ12. DevTools
**Decision:** `vite-plugin-vue-devtools` enabled in `vite.config.ts`. Provides real-time Pinia state inspection, component tree, and timeline.
**Rationale:** Essential for debugging the SSE update cycle and verifying `updateLocalState` fires correctly on each event.

### FQ13. Testing Strategy (Planned)
**Decision:** Three layers:
- **Unit** — pure functions in composables (`sse.ts` parsing, `api.ts` request construction)
- **Store** — Pinia store tests with mocked API and fake SSE events
- **Component** — Vitest + @vue/test-utils for views and components

**Rationale:** The dumb UI pattern makes component tests straightforward — provide a mock store, assert rendered output.

### FQ14. Notification Protocol — Toasts vs. Activity Pills
**Decision:** `store.ts`'s SSE callback branches on the incoming payload's `type` field before deciding what to do with it (see backend-side ARCHITECTURE.md Q32). A `{type: 'notification', ...}` payload is always server-authored and pushed straight to `addToast()` — this is how public activity pills ("Alex played ZEBRA for 42 pts", swaps, passes) and win-by-forfeit/timeout messages reach the client. Everything else is a full `GameStateOut` and goes through `updateLocalState()`, which additionally *derives* a second class of toast client-side by diffing `prev` against the incoming payload: first-strike overtime warnings (`overtime_count` 0→1), and pause/resume transitions. HTTP error responses (rejected moves, join failures) produce a third, purely local toast path via `catch` blocks in `GameView`/`LobbyView` — these never touch the SSE stream at all, matching the backend's "rejected-move feedback stays private to the mover" rule.
**Rationale:** Three sources, one sink (`addToast`) — `ToastFooter` doesn't need to know or care whether a message originated server-side, was derived from a state diff, or came from a failed fetch. Deriving pause/resume/overtime toasts from the diff (rather than the backend emitting a matching `notification` for every state change) keeps `game_broadcaster.notify()` reserved for messages that have no corresponding field in `GameState` at all (activity pills), instead of duplicating information the full-state push already carries.

### FQ15. Overlay Cards — Dismissible, Not Locked
**Decision:** `GameOverCard`, `GamePausedCard`, and `LeaveConfirmCard` are plain `v-if` overlays in `GameView.vue`, keyed off `store.phase` plus local `ref`s (`resultsOpen`, `showLeaveConfirm`) — not routes, not a generic modal manager. `GameOverCard` can be dismissed (closes to reveal the final board) and reopened via a "RESULT" button that appears in the header once dismissed. `LeaveConfirmCard` gates the Leave button only while `phase === 'playing'` — leaving mid-game calls `store.forfeit()` before navigating away; leaving a game that's already `finished`/`paused` skips the confirmation and forfeit call entirely, since there's no live turn to forfeit. Both `GameOverCard` and `LeaveConfirmCard` close on `Escape`.
**Rationale:** A game-over overlay that can't be dismissed blocks the player from actually looking at the final board, which is the thing they most want to see. Scoping the confirm-before-forfeit behavior to `playing` avoids a confusing "are you sure?" prompt for a game that has nothing left to lose.

### FQ16. Avatars
**Decision:** Ten bundled PNGs (`constants/avatars.ts`, `AVATARS: Record<string, string>` + `AVATAR_KEYS`), no upload/URL support. `LobbyView` lets the player pick one at create/join time; the chosen key is sent as `avatar` on `CreateGameRequest`/`JoinGameRequest`, stored on the domain `Player`, and returned in every `GameStateOut.players[].avatar`. The viewer's own avatar is also cached on `session` (`localStorage`) so it renders instantly before the first state payload arrives.
**Rationale:** A fixed, bundled set means zero moderation surface and zero upload/storage infrastructure for a feature that's purely cosmetic identity in a two-player game.

### FQ17. Turn Clocks — Local Ticking, Server-Anchored
**Decision:** `composables/useClocks.ts` renders a per-second countdown that re-anchors to `player.time_remaining_secs` every time a new `GameState` arrives (`serverBase` + `baseTimestamp`), and only runs its own `setInterval` while that player's `isActiveTurn` is true. Between server pushes it computes `serverBase - (Date.now() - baseTimestamp)` locally rather than waiting for the next SSE event to tick the displayed number down.
**Rationale:** This is purely cosmetic smoothing, not a violation of the dumb-client rule — `useClocks` never feeds a value back to the server or into any move payload; the actual elapsed time charged to a player is measured server-side in `turn_clock.py` at the moment a move is submitted (see `Turn.apply`'s `elapsed_secs` parameter). If the local tick and the server's charge ever disagree, the next state push simply re-anchors the display — there's no local state that can drift the game outcome.

---

## Key Engineering Constraints

1. **No local game mutations.** The frontend never computes scores, validates words, or modifies board state. Every mutation goes through the backend.
2. **One state pipe.** All GameState payloads route through `updateLocalState()` — HTTP response, route guard check, SSE event — no exceptions.
3. **Idempotent SSE.** `sse.ts` always closes before opening. No zombie EventSource instances.
4. **Explicit imports.** No `unplugin-auto-import` or `unplugin-vue-components`. Every dependency is explicitly imported.
5. **Session-bound SSE.** The transport composable is stateless; it receives a URL and a callback. All session logic lives in the store.
