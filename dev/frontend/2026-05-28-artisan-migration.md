## 2026-05-28 — Artisan Tabletop frozen as single theme; entire production frontend migrated to CSS custom properties

### What was built

**1. Tailwind v4 `@theme` tokens established as the single source of truth.**

The file `src/style.css` was expanded from a one-liner (`@import 'tailwindcss'`) to a full design-token block containing 30+ colour tokens, 4 font families, 4 border-radii, and 9 box-shadow values — all drawn from the Artisan Tableport palette (`src/style.css:9-90`). Every token is defined as a CSS custom property under the `@theme` directive, making them available as Tailwind utility classes (e.g. `bg-surface`, `font-serif`, `shadow-board`) and as raw `var(--color-*)` references anywhere in the codebase.

Global body defaults were set at `src/style.css:93-97`:
```css
body {
  background: #131313;
  color: #e5e2e1;
  font-family: 'EB Garamond', serif;
}
```

**2. Google Fonts moved to `index.html` `<link>` tag.**

Previously the prototype loaded EB Garamond and Work Sans via a render-blocking `@import` in the component `<style>` block. The import was removed from `PrototypeUI.vue` and replaced with a `<link>` in `frontend/index.html:10-12`, with `preconnect` hints for both `fonts.googleapis.com` and `fonts.gstatic.com`.

**3. Multi-theme system frozen.**

Three files were gutted or rewritten to remove theme-switching:

- `src/constants/board.ts` — The `BOARD_THEMES` array (3 themes: Classic, Dark, High Contrast) and the `getTheme()` lookup function were removed. Only `PREMIUM_LAYOUT` (the 15×15 grid builder) and `PREMIUM_LABELS` (a `Record<PremiumType, string>`) remain. The `BoardTheme` and `SquareTheme` types still exist in `types/game.ts` but are unused.

- `src/composables/useTheme.ts` — Reduced to a no-op stub returning `{ themeName: 'Artisan', setTheme: () => {}, availableThemes: [] }`. No localStorage, no watchers, no `getTheme()` call.

- `src/components/settings/ThemePicker.vue` — Orphaned (no longer imported by any view). Retained as a file but unreachable.

**4. `GameBoard.vue` rewritten to use CSS custom properties directly.**

At `src/components/game/GameBoard.vue`, the component no longer accepts a `themeName` prop and no longer imports `getTheme()`. Premium squares use scoped CSS classes (`cell--dl`, `cell--tl`, `cell--dw`, `cell--tw`, `cell--center`) that reference `var(--color-premium-*-bg)` and `var(--color-premium-*-label)`. The board container uses `var(--shadow-board)`, `var(--radius-board)`, and a `linear-gradient` background via CSS vars. Cells use `border-collapse: separate` with `border-spacing: 1px` for proper cell gaps (replacing the old `border-collapse` that prevented individual border-radius from showing). Placed tiles render EB Garamond letters over `var(--color-placed-tile-bg)` with point subscripts. Ghost tiles use a translucent beige with emerald border.

**5. `PlayerPanel.vue` rebuilt to match spec.**

At `src/components/ui/PlayerPanel.vue`, the panel now implements the three-block vertical layout: a connection-dot row (name + 6px dot), a hero score (36px 900 weight white), and a micro-label with mono clock. The `dotState` computed property at line 17 returns background/shadow/animation based on three states: green+dlow for active turn, pulsing emerald for connected-but-waiting, muted gray for disconnected. Card `opacity: 0.5` applies only when `player?.connected === false`. Active turn triggers `borderTop: 2px solid #10b981` at line 40.

**6. `TileRack.vue` restyled with overshoot transitions.**

At `src/components/game/TileRack.vue`, a rack wrapper div with gradient background, `1px solid var(--color-outline-variant)`, and `inset 0 1px 2px` shadow was added. Tiles are 44×44px with gradient fills and `cubic-bezier(0.34, 1.56, 0.64, 1)` transitions. The `tileStyle()` function returns a full style object per state (default, hovered via `tileHover()` mouseenter/mouseleave, selected, swap-highlighted, placed-dimmed). The shuffle button from the prototype was not ported (not part of the production component contract).

**7. `MoveControls.vue` changed from Tailwind colours to scoped CSS classes.**

At `src/components/ui/MoveControls.vue`, four scoped CSS classes replace inline Tailwind: `.btn--submit` (brass gradient `var(--color-outline) → #8a7d7b`, filled shadow), `.btn--outline` (transparent bg, `1px solid var(--color-outline-variant)`, hover fills to `surface-container-high`), `.btn--swap-active` (brass outline), and `.btn--forfeit` (`var(--color-tertiary-container)` bg with `var(--color-tertiary)` border).

**8. `LobbyView.vue` recoloured to dark walnut and brass.**

At `src/views/LobbyView.vue`, the card background changed from `bg-neutral-800` to `var(--color-primary-container)` (dark walnut `#3e2723`), with a `1px solid var(--color-outline)` brass border and `var(--shadow-card)`. The title uses EB Garamond 32px in `var(--color-primary)`. The tab bar uses `var(--color-surface-container-lowest)` with active tabs filled in `var(--color-outline)`. All buttons (both Create and Join) use the brass gradient. Inputs use `var(--color-surface-container-lowest)` with `inset 0 2px 4px` shadows. Font references switched from Tailwind classes to `var(--font-serif)` and `var(--font-sans)`.

**9. `ToastFooter.vue` restyled to a single 30px bar.**

At `src/components/ui/ToastFooter.vue`, the stacked toast-card layout was replaced with a single fixed bar (30px height, `var(--color-surface-container-low)` background, `border-top: 1px solid var(--color-outline-variant)`). Only the most recent toast is shown, with a coloured dot per type (error=tertiary, success=green, info=outline). Still reads from `store.toasts` and respects the existing auto-dismiss mechanism.

**10. `GameView.vue` gained bag indicator and game-over overlay.**

At `src/views/GameView.vue`, two new elements added:
- A bag indicator pill above the board (importing `bag.svg` from `src/assets/bag.svg`, showing `store.game.bag_remaining`), styled identically to the prototype's pill badge.
- A game-over overlay triggered by `store.phase === 'finished'`, showing the winner's name/score in EB Garamond/Work Sans, a final-scores list with winner highlighted in primary colour, and a "Play Again" brass button.

The Theme button and ThemePicker were removed. The `Header code string` was changed from `Game {{ code }}` to `GAME · {{ code }}` in Work Sans 12px 700. The main content area gained `padding-bottom: 80px` to insulate controls from the fixed notification bar.

**11. `PrototypeUI.vue` synced to use CSS custom properties.**

The prototype's Google Fonts `@import` was removed (fonts now served from `index.html`). All 47 font-family inline style references were converted to `var(--font-serif)`, `var(--font-sans)`, `var(--font-panel)`, and `var(--font-mono)`. The `cellStyle()` function was updated to return CSS var references (`var(--color-premium-dl-bg)`, etc.) instead of hardcoded hex values.

### Decisions taken

**Decision 1: Freeze multi-theme selection; hardcode Artisan as the only theme.**

Three themes (Classic, Dark, High Contrast) existed in `constants/board.ts` with Tailwind utility-class values. The decision was made to abandon them entirely rather than add a fourth Artisan theme alongside them. Rationale: maintaining n themes × m components creates combinatorial overhead, and the Artisan palette is specific enough that the other themes would never match its visual standard. The `BoardTheme` type and `useTheme` composable are kept as dead stubs to avoid breaking imports across the codebase until a dedicated cleanup pass.

**Decision 2: CSS custom properties + Tailwind v4 `@theme` over a JavaScript theme object.**

Alternative was to keep the `colors` object pattern used in the prototype (a reactive plain object with kebab-case keys). Rejected because: (a) `@theme` tokens generate Tailwind utility classes for free, (b) CSS vars work in both `<style scoped>` and inline `:style` bindings, and (c) the prototype can reference `var(--color-*)` directly without importing or passing props. The downside — CSS vars cannot be used in `<script>` computations — is mitigated by keeping the small number of JS-side colour references (e.g., `notifs` dot colours) as hardcoded strings.

**Decision 3: Scoped CSS classes over inline styles for component-specific styling.**

`MoveControls.vue` and `GameBoard.vue` both use `<style scoped>` classes (`.btn--submit`, `.cell--dl`) rather than inline `:style` objects. This keeps the templates readable and allows pseudo-classes (`:hover`, `:disabled`). The trade-off is that dynamic values (e.g., which cell classes to apply) require computed strings or conditional class binding, which adds a small amount of script complexity.

**Decision 4: Keep `ToastFooter` reading from store.toasts rather than building a separate cycling API.**

The prototype's notification system cycles through 3 hardcoded mock notifications on a timer. For production, the store's `addToast`/auto-dismiss mechanism is already used by `LobbyView`, `GameView`, and `MoveControls`. Rewriting to a cycling bar would require a new composable or store changes. Instead the existing toast store was kept, with the display restyled to show only the single most recent toast. This is a pragmatic compromise — the cycling behaviour can be added later if needed.

### Problems identified

**Problem 1: `ThemePicker.vue` is orphaned but still ships in the bundle.**

The file `src/components/settings/ThemePicker.vue` is no longer imported by any view but remains in the codebase. It imports `BoardTheme` from `types/game.ts`, which prevents that type from being removed without deleting the file. Tree-shaking should exclude it from the production bundle since it has no entry-point references, but it adds noise. *Open.*

**Problem 2: `BoardTheme` and `SquareTheme` types are dead.**

`types/game.ts:110-118` (BoardTheme) and `103-108` (SquareTheme) are no longer used by any component. Removing them requires also removing or replacing the import in `ThemePicker.vue`. *Open.*

**Problem 3: No loading/skeleton states for the board or game-over overlay.**

The `GameBoard.vue` empty state at line 95 shows a simple "Loading board…" text; the game-over overlay appears instantly with no transition animation. The prototype has a `fadeIn` keyframe for the overlay but it wasn't ported. *Open.*

**Problem 4: Bag indicator image path assumes asset is at `src/assets/bag.svg`.**

Both `PrototypeUI.vue` and `GameView.vue` import `bagImg` from `'../assets/bag.svg'`. If the asset is moved or renamed, both break. *Open.*

**Problem 5: No transition on player panel `opacity` disconnect.**

Identical to the prototype problem: `PlayerPanel.vue:37` has `:style="{ opacity: player?.connected !== false ? 1 : 0.5 }"` with no CSS transition. The value jumps instantly. *Open.*

### Current state of the codebase

**Frontend — fully migrated to Artisan tokens.**

All 6 production components and 2 views now reference CSS custom properties and/or scoped classes derived from the `@theme` block. No component imports `BOARD_THEMES`, `getTheme()`, or `useTheme()` for styling. The prototype is in sync.

- `style.css` — `@theme` token block (90 lines), body defaults
- `index.html` — Google Fonts via `<link>`, title "NEO Scrabble"
- `constants/board.ts` — `PREMIUM_LAYOUT` + `PREMIUM_LABELS` only (was 78 lines, now 27)
- `composables/useTheme.ts` — No-op stub (6 lines)
- `components/game/GameBoard.vue` — Scoped CSS classes, CSS var references, 195 lines
- `components/game/TileRack.vue` — Scoped CSS class for wrapper, inline style objects per tile, 135 lines
- `components/ui/PlayerPanel.vue` — `dotState` computed, three-block layout, 105 lines
- `components/ui/MoveControls.vue` — Scoped CSS button classes, 120 lines
- `components/ui/ToastFooter.vue` — Single bar, store-driven, 31 lines
- `views/LobbyView.vue` — Dark walnut card, brass elements, 160 lines
- `views/GameView.vue` — Bag indicator, game-over overlay, no theme picker, 195 lines
- `views/PrototypeUI.vue` — Synced to CSS vars, no Google Fonts import, ~890 lines

**Backend — unchanged from session 1.**

All 5 game endpoints in `routes/games.py` and the SSE endpoint in `routes/events.py` remain stubs. No CORS middleware. The frontend cannot make successful API calls.

### References

| File | Key locations |
|------|---------------|
| `frontend/src/style.css` | `@theme` block (L9–90), body defaults (L93–97) |
| `frontend/index.html` | Google Fonts `<link>` (L10–12) |
| `frontend/src/constants/board.ts` | `PREMIUM_LAYOUT` (L23), `PREMIUM_LABELS` (L27) |
| `frontend/src/composables/useTheme.ts` | No-op stub (L8–14) |
| `frontend/src/components/game/GameBoard.vue` | Scoped cell classes (L87–138), `handleCellClick` (L38–49), blank picker (L87–131) |
| `frontend/src/components/game/TileRack.vue` | `tileStyle()` (L17–89), `tileHover()` (L91–104), rack container style (L129–134) |
| `frontend/src/components/ui/PlayerPanel.vue` | `dotState` (L17–29), template blocks (L38–99) |
| `frontend/src/components/ui/MoveControls.vue` | Scoped `.btn` classes (L74–120) |
| `frontend/src/components/ui/ToastFooter.vue` | Single-bar template (L10–31) |
| `frontend/src/views/LobbyView.vue` | Card styling (L49–59), form inputs (L73–160) |
| `frontend/src/views/GameView.vue` | Bag indicator (L102–112), game-over overlay (L143–195), header (L70–91) |
| `frontend/src/views/PrototypeUI.vue` | `cellStyle()` with CSS var refs (L37–51), font-family replaced across template |
| `frontend/src/components/settings/ThemePicker.vue` | Orphaned (L1–50) |
| `frontend/src/types/game.ts` | `BoardTheme` (L110–118), `SquareTheme` (L103–108) — both dead |
