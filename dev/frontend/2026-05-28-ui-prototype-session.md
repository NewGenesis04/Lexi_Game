## 2026-05-28 — UI prototype and design direction pivot from flat minimal to skeuomorphic luxury

### What was built

**Three new files were created:**

1. **`frontend/src/views/PrototypeUI.vue`** — a self-contained, single-file prototype that renders three switchable screens (Lobby, Game, Game Over) using mock data. No Pinia store, no API calls, no backend dependency. The view is gated behind a throwaway route and is not connected to any production data flow. The `Screen` type (`lobby | game | finished`) determines which section renders; a fixed-position pill switcher at the top of the viewport cycles between them.

2. **`frontend/src/router/index.ts`** — the prototype route was registered at `routes[2]`:
   ```ts
   { path: '/prototype/ui', name: 'prototype-ui', component: () => import('../views/PrototypeUI.vue') }
   ```

3. **`docs/UI_DESIGN_BRIEF.md`** — rewritten to replace the original flat-minimal design language (which specified "no gradients, no drop-shadows") with a premium system based on glass morphism, layered shadows, gradient fills, and hover animations. The rewrite preserved the structural layout sections (Lobby, Game Board, Game Over, Notification Bar, Settings) but replaced every visual specification.

**Two design systems were prototyped back-to-back in the same file:**

- **Premium Dark (first iteration):** Tailwind utility classes throughout. Gradients on premium cells (`from-blue-900 to-blue-950` for DL, etc.), glass morphism via `backdrop-blur-xl` on player panels and the notification bar, glossy amber tiles with `shadow-lg`, rainbow gradient on the lobby title, `backdrop-blur-2xl` on the game-over overlay, and a `@keyframes fadeIn` animation for the overlay entrance.

- **The Artisan Tabletop System (second iteration, current):** A complete replacement of every inline style to match an external design system specification. The colour palette is hardcoded in a reactive `colors` object in `PrototypeUI.vue:13-33` from a Material-like token set (`surface: '#131313'`, `primary-container: '#3e2723'` (Dark Walnut), `outline: '#9c8d8b'` (Brass), `tertiary-container: '#5a1200'` (Copper)). Typefaces are loaded via Google Fonts: EB Garamond for lettering, Work Sans for labels and numbers. CSS box-shadows use tight, high-opacity values (`inset 0 1px 2px rgba(0,0,0,0.3)` for carved recesses, `0 1px 3px rgba(0,0,0,0.4)` for physical tokens). Borders are 1px solid `colors.outline` to simulate brass inlay.

The board grid in the Artisan iteration uses the `cellStyle()` function at `PrototypeUI.vue:36-51` to map premium types (1=DL, 4=TL, 2=DW, 3=TW, 5=★) to artisan material colours rather than Tailwind gradient strings. Placed tiles render as `surface-container-high` plaques with engraved-looking EB Garamond letters and Work Sans point subscripts at bottom-right.

### Decisions taken

**Decision 1: Single-file prototype over component decomposition.**
The prototype skill (`prototype/UI.md`) recommends creating several structurally distinct variants switchable via `?variant=` search param and a floating bottom bar. This was rejected in favour of a single monolithic `.vue` file containing all three screens inline. Rationale: the user's brief was prescriptive enough that the design direction was already settled — the question was not "which layout?" but "does this texture feel right?" A single file reduces iteration friction: every style change is in one place, no prop-drilling across components, no route-guard wiring. The downside is this file is 653 lines and cannot be decomposed into production components without rewriting.

**Decision 2: Inline styles over Tailwind utility classes for the Artisan iteration.**
The Premium Dark iteration used Tailwind classes exclusively (`bg-gradient-to-br`, `shadow-2xl`, `backdrop-blur-xl`). The Artisan iteration switched to Vue `:style` bindings with a shared `colors` object. Rationale: the Artisan palette has no overlap with Tailwind's built-in colour scale (no `amber-50`, no `neutral-900` — only arbitrary hex values like `#131313` and `#3e2723`). Tailwind v4's CSS-first configuration could have been extended via `@theme` in `style.css`, but that would pollute a global config file for a throwaway prototype. Inline styles keep the prototype self-contained.

**Decision 3: Mock data embedded in the prototype rather than pulling from the Pinia store.**
The production `LobbyView.vue` and `GameView.vue` both read from `useGameStore()`. The prototype defines its own `placedTiles` array, `rackTiles` array, and `PREMIUM` grid layout. Rationale: zero backend dependency. The prototype runs with `pnpm dev`, no FastAPI, no Redis, no SSE. The tile placement data mirrors the production `GameState.board` shape but is purely decorative.

**Decision 4: Embed Google Fonts via `@import` in the component `<style>` block.**
The Artisan spec requires EB Garamond and Work Sans. The import is at `PrototypeUI.vue:647`. Alternative considered: downloading and self-hosting, or adding a `<link>` to `index.html`. Rejected because (a) the prototype is throwaway and (b) the production design brief (still in `docs/UI_DESIGN_BRIEF.md`) specifies the system font stack — these fonts will never ship to production.

**Decision 5: Backend `main.py` was not modified (reverted).**
An earlier attempt added `CORSMiddleware` to `packages/backend-api/src/backend_api/main.py` to fix a `TypeError: NetworkError` during room creation. This was reverted when the user clarified the prototype is frontend-only and should not require a running backend. The network error originated from the production `LobbyView` calling `store.createGame()` → `fetch('http://localhost:8000/games')` with no backend running — expected behaviour, not a bug.

### Problems identified

**Problem 1: Backend route handlers are stubs.**
In `packages/backend-api/src/backend_api/routes/games.py`, all five endpoints (`create_game`, `join_game`, `submit_move`, `forfeit_game`, `get_game`) are empty function bodies containing only `...`. The SSE endpoint in `routes/events.py` is similarly a stub. Calling any of these over HTTP returns a 500 Internal Server Error with no body. This is open — the routes were presumably deferred for later implementation. The frontend's `LobbyView.handleCreate()` (at `LobbyView.vue:16`) will fail with a network error when it tries to `POST /games` against a running backend because the handler has no return statement.

**Problem 2: No CORS middleware on the backend.**
The FastAPI app in `main.py` (8 lines) does not configure `CORSMiddleware`. When the frontend dev server runs on `localhost:5173` and the backend on `localhost:8000`, the browser's same-origin policy blocks all cross-origin requests. This is open — it was never configured because the backend routes are not yet functional.

**Problem 3: Prototype tile rack selection is decorative only.**
The `selectedIndex` ref at `PrototypeUI.vue:105` toggles visual state (ring, lift, colour swap) but does not feed into any board-placement logic. There is no composable equivalent to `usePendingMove.ts` wired in. This is by design for a visual prototype but means the interaction model cannot be validated from this file.

**Problem 4: The board theme system (`constants/board.ts`) is not used by the prototype.**
The prototype duplicates the premium layout grid (the 15×15 integer matrix at `PrototypeUI.vue:57-73`) and defines its own cell styling in `cellStyle()` rather than consuming `PREMIUM_LAYOUT` and `BOARD_THEMES` from `frontend/src/constants/board.ts`. This is open as a code-quality concern but acceptable for a throwaway prototype.

**Problem 5: Font loading adds a render-blocking request.**
The Google Fonts `@import` in the component style block will block rendering until the stylesheet is fetched. In production this would be visible as a flash of invisible text (FOIT). Acceptable for prototype.

### Current state of the codebase

**Backend (FastAPI) — fully stubbed.**

- `backend-api/src/backend_api/main.py` — FastAPI app instantiated, two routers included. No middleware. 8 lines.
- `backend-api/src/backend_api/routes/games.py` — five endpoints, all `async def ...: ...`. 30 lines.
- `backend-api/src/backend_api/routes/events.py` — one endpoint (`GET /events`), stubbed. 11 lines.
- `backend-api/src/backend_api/services/game_service.py` — file exists, not read during this session.
- `backend-api/src/backend_api/repositories/game_repo.py` — file exists, not read.
- `backend-api/src/backend_api/game_manager.py` — file exists.
- `backend-api/src/backend_api/sse_manager.py` — file exists.
- `backend-api/src/backend_api/session.py` — file exists.

**Game engine — not examined during this session.**

- `game-engine/src/game_engine/board.py`, `scoring.py`, `bag.py`, `dictionary.py`, `models.py` — presumed fully or partially implemented, not read.

**Frontend (Vue SPA) — two production views, one throwaway route.**

- `frontend/src/views/LobbyView.vue` — fully implemented with wired Pinia calls. Two-tab form (Create / Join). Calls `store.createGame()` and `store.joinGame()`. Cannot function without a running backend.
- `frontend/src/views/GameView.vue` — fully implemented composition root. Imports `GameBoard`, `TileRack`, `PlayerPanel`, `MoveControls`, `ThemePicker`. Consumes `useGameStore()` and `usePendingMove()`. Cannot function without a running backend.
- `frontend/src/views/PrototypeUI.vue` — throwaway prototype, 653 lines. Self-contained mock data, no store dependency. Three-screen switcher with Artisan Tabletop styling.

**Frontend components — all production, all flat-styled.**

- `components/game/GameBoard.vue` — 15×15 table grid, theme-driven via `constants/board.ts`. Renders ghost tiles, handles blank-letter picker overlay. No premium styling.
- `components/game/TileRack.vue` — 7-slot horizontal strip, amber-100 tiles, ring on selection. 42 lines.
- `components/ui/PlayerPanel.vue` — score, clock, connection dot, "Current turn" label. neutral-800 surface, no glass morphism. 42 lines.
- `components/ui/MoveControls.vue` — Submit/Clear/Swap/Pass/Forfeit buttons. Solid neutral-600 and blue-600 backgrounds. 97 lines.
- `components/ui/ToastFooter.vue` — fixed-bottom toast list. Solid red/green/neutral backgrounds. 27 lines.
- `components/settings/ThemePicker.vue` — exists but not read during this session.

**Frontend infrastructure — all implemented.**

- `router/index.ts` — three routes (`/`, `/game/:code`, `/prototype/ui`).
- `router/guards.ts` — `gameGuard` (read during prior session, not shown here).
- `stores/game.ts` — Pinia store with `game`, `session`, `toasts`, `connected` state. `createGame`, `joinGame`, `submitMove`, `forfeit`, `fetchGame` actions. SSE lifecycle methods. 144 lines.
- `services/api.ts` — `fetch()`-based HTTP client, `ApiRequestError` class, five typed methods. 69 lines.
- `composables/sse.ts` — EventSource lifecycle manager (read during prior session, not shown here).
- `composables/usePendingMove.ts` — click-then-click tile placement state machine. Ghost tiles, swap mode, blank letters. 165 lines.
- `composables/useTheme.ts` — theme persistence via localStorage, three themes from `constants/board.ts`. 31 lines.
- `types/game.ts` — 21 interfaces/types including `GameState`, `PlayerState`, `BoardTheme`, `MovePayload`. 118 lines.
- `constants/board.ts` — `buildGrid()` generates the 15×15 premium layout; `BOARD_THEMES` array with Classic, Dark, High Contrast; `getTheme()` lookup. 78 lines.
- `App.vue` — `<router-view>` + `ToastFooter`. 8 lines.
- `main.ts` — `createApp`, Pinia, Router mount. 10 lines.

**Documentation:**

- `docs/ARCHITECTURE.md` — 284 lines, 31 engineering decisions (Q1–Q31). Covers tile set, word lists, SSE design, Redis data model, disconnect state machine, deployment.
- `docs/FRONTEND.md` — 234 lines, 13 frontend decisions (FQ1–FQ13). Covers framework choice, CSS strategy, Pinia store, component architecture, SSE lifecycle.
- `docs/UI_DESIGN_BRIEF.md` — rewritten this session, 255 lines. Premium design system documentation with gradients, glass morphism, shadows, animation specs, per-component styling.
- `docs/RULES.md` — exists but not read during this session.

### References

| File | Key locations |
|------|---------------|
| `frontend/src/views/PrototypeUI.vue` | `colors` object (L13–33), `cellStyle()` (L36–51), `PREMIUM` grid (L57–73), `placedTiles` (L82–93), `rackTiles` (L95–103), `selectedIndex` (L105), screen switcher (L124–152), board table (L361–414), tile rack (L417–456), controls (L458–547), game-over overlay (L566–640), Google Fonts `@import` (L647) |
| `frontend/src/router/index.ts` | `routes[2]` prototype registration (L18–22) |
| `docs/UI_DESIGN_BRIEF.md` | Premium Design System section (L36–71), Board (L145–158), Controls (L172–187), Design Principles (L247–255) |
| `packages/backend-api/src/backend_api/main.py` | FastAPI app (L1–8), no CORS middleware |
| `packages/backend-api/src/backend_api/routes/games.py` | Five stubbed endpoints (L8–30) |
| `packages/backend-api/src/backend_api/routes/events.py` | Stubbed SSE endpoint (L10–11) |
| `frontend/src/views/LobbyView.vue` | `handleCreate()` (L16–27), `handleJoin()` (L29–40) |
| `frontend/src/views/GameView.vue` | Composition root (L1–69), template layout (L72–143) |
| `frontend/src/stores/game.ts` | `useGameStore` (L19–144), `createGame()` (L63–72), `joinGame()` (L74–79) |
| `frontend/src/services/api.ts` | `request()` (L12–25), `createGame()` (L37–43), base URL default (L10) |
| `frontend/src/composables/usePendingMove.ts` | `GhostTile` interface (L4–8), `buildPlacePayload()` (L20–34), `selectRackTile()` (L50–60), `tryPlaceTile()` (L62–76) |
| `frontend/src/composables/useTheme.ts` | `themeName` ref (L16), `setTheme()` (L26–28), `availableThemes` (L30) |
| `frontend/src/types/game.ts` | `GameState` (L46–61), `PlayerState` (L26–34), `BoardTheme` (L110–118), `PremiumType` (L101) |
| `frontend/src/constants/board.ts` | `buildGrid()` (L5–21), `BOARD_THEMES` (L25–74), `getTheme()` (L76–78) |
| `frontend/src/components/game/GameBoard.vue` | `cellClasses()` (L41–54), `cellContent()` (L56–68), `handleCellClick()` (L25–39) |
| `frontend/src/components/game/TileRack.vue` | `tileClasses()` (L16–22) |
| `frontend/src/components/ui/PlayerPanel.vue` | Template (L10–41) |
| `frontend/src/components/ui/MoveControls.vue` | `handleSubmit()` (L22–32), `handlePass()` (L34–43), `handleForfeit()` (L45–54) |
| `frontend/src/components/ui/ToastFooter.vue` | Toast rendering (L7–27) |
| `frontend/src/App.vue` | `<router-view>` + `ToastFooter` (L5–8) |
| `frontend/src/main.ts` | App bootstrap (L1–10) |
| `docs/FRONTEND.md` | FQ1–FQ13 decisions (L125–224), directory structure (L84–119) |
| `docs/ARCHITECTURE.md` | Q1–Q31 decisions (L107–284), data flow diagrams (L8–62) |
