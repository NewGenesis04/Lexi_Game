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
    │   ├── LobbyView.vue            # Create / Join tabbed form
    │   └── GameView.vue             # Board composition root
    └── components/
        ├── game/
        │   ├── GameBoard.vue        # 15×15 grid
        │   └── TileRack.vue         # Current player's tiles
        ├── ui/
        │   ├── PlayerPanel.vue      # Score, name, clock, connected status
        │   ├── MoveControls.vue     # Pass, Forfeit (place/swap TBD)
        │   └── ToastFooter.vue      # Fixed-bottom error/info toasts
        └── settings/                # Future: dictionary/time/game config views
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
**Decision:** `vue-router` with two routes:
| Path | View | Guard | Purpose |
|------|------|-------|---------|
| `/` | `LobbyView` | None | Create or join a game |
| `/game/:code` | `GameView` | `gameGuard` | Active game board |

`gameGuard` (`router/guards.ts`):
1. Tears down any existing SSE connection
2. Calls `store.fetchGame(code)`
3. On success — opens SSE stream, enters route
4. On 404 — pushes error toast, calls `store.reset()`, redirects to `/`
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
**Decision:** Components never call the API directly. They read from the store and emit user gestures:
- `LobbyView` — calls `store.createGame()` / `store.joinGame()`, navigates on success
- `GameView` — composition root; lays out board, rack, panels
- `GameBoard` — renders 15×15 grid from `store.game.board`
- `TileRack` — renders `store.myPlayer.rack`
- `PlayerPanel` — displays score, clock, connection status for a player
- `MoveControls` — pass/forfeit buttons (place/swap added later)
- `ToastFooter` — renders `store.toasts` array, fixed bottom, auto-dismiss after 5s

Components are organized by domain: `components/game/`, `components/ui/`, `components/settings/`.
**Rationale:** Store-driven rendering makes the UI a pure function of `gameState`. Components are trivially testable.

### FQ10. Toast System
**Decision:** `store.addToast(text, type)` pushes a `ToastMessage` with auto-generated ID and 5-second TTL. `ToastFooter` renders the array fixed at the bottom of the viewport.
**Rationale:** Centralized toast state means route guards, views, and the store all use the same error-reporting path. No ad-hoc alert() or inline error divs.

### FQ11. Tile Placement (Planned)
**Decision:** Hybrid interaction — click tile from rack to select it, then click a board cell to place it. A preview layer shows ghost tiles before submission. The final move payload is an explicit array of `{row, col, letter, plays_as?}` objects sent via `store.submitMove()`.
**Rationale:** Click-then-click is the most intuitive for desktop. `plays_as` for blanks is handled via a dropdown on the placed tile. Implementation deferred until the board component is iterated on.

### FQ12. DevTools
**Decision:** `vite-plugin-vue-devtools` enabled in `vite.config.ts`. Provides real-time Pinia state inspection, component tree, and timeline.
**Rationale:** Essential for debugging the SSE update cycle and verifying `updateLocalState` fires correctly on each event.

### FQ13. Testing Strategy (Planned)
**Decision:** Three layers:
- **Unit** — pure functions in composables (`sse.ts` parsing, `api.ts` request construction)
- **Store** — Pinia store tests with mocked API and fake SSE events
- **Component** — Vitest + @vue/test-utils for views and components

**Rationale:** The dumb UI pattern makes component tests straightforward — provide a mock store, assert rendered output.

---

## Key Engineering Constraints

1. **No local game mutations.** The frontend never computes scores, validates words, or modifies board state. Every mutation goes through the backend.
2. **One state pipe.** All GameState payloads route through `updateLocalState()` — HTTP response, route guard check, SSE event — no exceptions.
3. **Idempotent SSE.** `sse.ts` always closes before opening. No zombie EventSource instances.
4. **Explicit imports.** No `unplugin-auto-import` or `unplugin-vue-components`. Every dependency is explicitly imported.
5. **Session-bound SSE.** The transport composable is stateless; it receives a URL and a callback. All session logic lives in the store.
