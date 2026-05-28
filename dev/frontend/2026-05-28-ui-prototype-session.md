## 2026-05-28 — UI prototype refinements: connection-state semantics, notification-bar positioning, tile-rack shuffle

### What was built

This session corrected three behavioural issues in the existing Artisan Tabletop prototype and added one new interaction:

**1. Player panel connection-state dot semantics (corrected).**

The player panels at `PrototypeUI.vue:434-468` (opponent) and `PrototypeUI.vue:727-762` (current player) had the connection-indicator dot and card opacity wired to the wrong signal. The opacity was previously gated on `players.opp.turn` (whether it was their turn) instead of `players.opp.connected`. The dot colour was binary: green for turn, gray otherwise.

Both panels were corrected to the three-state model specified in the design brief:
- **Connected + active turn:** dot is solid green (`#10b981`) with a `0 0 6px rgba(16,185,129,0.5)` glow. Card opacity = 1. Top border is `2px solid #10b981` (emerald).
- **Connected + waiting:** dot is emerald (`#34d399`) with a `pulse 2s ease-in-out infinite` animation (keyframe at `PrototypeUI.vue:886-889`). Card opacity = 1. Top border is standard (`1px solid rgba(96,96,96,0.3)`).
- **Disconnected:** dot is gray (no glow, no animation). Card drops to `opacity: 0.5`.

The opacity bindings at `PrototypeUI.vue:435` and `PrototypeUI.vue:728` both changed from `player.turn` to `player.connected`.

The `pulse` keyframe was added at `PrototypeUI.vue:886-889`:
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

**2. Notification bar repositioned from flow layout to fixed overlay.**

The notification bar at `PrototypeUI.vue:766-791` was originally a flex child in the `flex-col` game layout. When it appeared, it pushed the board, rack, and controls upward, causing vertical overflow and requiring scroll to reach the controls.

The bar was changed from inline-flow to `fixed bottom-0 left-0 right-0 z-50` at `PrototypeUI.vue:773`. It now overlays the viewport as a 30px strip without affecting document flow. The `slideUp` animation (`PrototypeUI.vue:881-884`) slides it in from below the viewport edge.

**3. Rack tiles made reactive; shuffle function added.**

The `rackTiles` array at `PrototypeUI.vue:96-104` was a plain `const` array, which meant Vue reactivity could not detect mutations. It was wrapped in `ref()` (import already present at line 2).

The `shuffleRack()` function at `PrototypeUI.vue:109-117` performs a Fisher-Yates shuffle on a copy of `rackTiles.value` and reassigns the ref. It also clears `selectedIndex.value` to `null`.

A shuffle button was added at `PrototypeUI.vue:602-631` as the last element in the rack's flex row. It is a 36×36px transparent button with a `1px solid #504442` border and an inline SVG icon showing crossed arrows (two polyline arrowheads with connecting lines). The icon uses `currentColor` and inherits `colors.outline` (`#9c8d8b`). On click it calls `shuffleRack()`.

**4. Design brief rewritten to match implemented reality.**

The file `docs/UI_DESIGN_BRIEF.md` was entirely rewritten. The previous version described a flat-minimal design with Tailwind gradients, glass morphism via `backdrop-blur`, and a general Tailwind-centred palette. The new version documents every hex value, every font stack, every box-shadow string, and every interaction state as they exist in `PrototypeUI.vue`. It is structured by screen (Lobby, Game, Game Over) and within each screen by component, with tables for typography and palette tokens. It supersedes the earlier rewrite from session 1 because the earlier version was aspirational; this one is descriptive.

### Decisions taken

**Decision 1: `opacity: 0.5` signals disconnected, not "not your turn".**

The prototype's initial implementation mapped `opacity: 0.5` to `!player.turn`, which meant the waiting player's card was always dimmed. This was a misreading of the spec: the spec uses the turn indicator exclusively via the emerald top-border, not via card opacity. The opacity half-toning is reserved for the disconnected state, signalling to the player that their opponent has dropped off. No alternative was considered — this was a straightforward bug fix.

**Decision 2: Notification bar stays `fixed` (overlay) rather than inline.**

The previous session had moved the notification bar from `fixed bottom-0` to inline flow to avoid covering the controls. But inline flow caused the entire game layout to shift on notification appearance, creating a scroll requirement. The bar was returned to `fixed bottom-0 left-0 right-0 z-50` at 30px height. At 30px it is slim enough to overlay only the bottom edge of the game area — it does not cover any controls because the controls sit above that line in the flex column. The trade-off (content hidden behind the bar when present) is acceptable because the bar auto-dismisses after 3.5 seconds and is click-to-dismiss.

**Decision 3: `rackTiles` wrapped in `ref()` for reactive shuffle.**

The `rackTiles` array was initially declared as `const rackTiles = [...]` — a plain JavaScript array. The shuffle button required mutating this array, but Vue 3 only tracks changes to `ref()` or `reactive()` objects. Wrapping in `ref()` was the minimal change. Alternative considered: using `reactive()`, but the array is the only reactive data it holds, and `ref` is semantically clearer for a single value. `shuffleRack()` replaces the entire array (`rackTiles.value = arr`) after shuffling a copy, rather than mutating in-place, so Vue's change detection fires correctly.

**Decision 4: Design brief converted from spec to documentation.**

The earlier design brief was a forward spec — it described what should be built. This session rewrote it to describe what exists. The structure stays the same (screens and components as sections) but every value is taken directly from the `colors` object and inline styles in `PrototypeUI.vue`. This was not a debated decision; the user explicitly requested the brief be updated to "the current design language of the prototype" so they could use it as a starting point for production.

### Problems identified

**Problem 1: No `opacity` transition on player panels for disconnect state.**

When `players.opp.connected` toggles to `false`, the `opacity` jumps from 1 to 0.5 instantly because there is no CSS transition on the wrapper div at `PrototypeUI.vue:435`. The same applies to the current player panel at line 728. This is currently untestable because the mock data always has both players connected. Trivial to fix by adding `transition: 'opacity 0.3s'` to the wrapper style object. *Resolved?* No change made — purely cosmetic and blocked on having a disconnect trigger to drive it.

**Problem 2: `players` object is not reactive.**

The mock player data at `PrototypeUI.vue:121-124` is a plain object literal assigned to `const players`. Changing `players.opp.connected` or `players.opp.turn` will never trigger a re-render. This matters because the dot colour, animation, card opacity, and top-border colour all depend on these fields. In a true prototype with toggles or simulated state changes, this would need to be `reactive()` or individual `ref()`s. Currently it does not manifest because the data never changes. *Open.*

**Problem 3: Notification cycling timer does not handle tab visibility.**

The `notifTimer` interval at `PrototypeUI.vue:187-197` runs unconditionally every 3.5 seconds. If the browser tab is backgrounded, browsers throttle `setInterval` to 1 tick per minute. On return, the queue of backlogged ticks fires rapidly, flashing through all notifications. The fix would use `requestAnimationFrame`-based scheduling or check `document.visibilityState`. *Open.*

**Problem 4: Board labels use fixed column letter array, not the shared constant.**

The `COL_LABELS` constant at `PrototypeUI.vue:5` duplicates the column letters. The production codebase has this in `constants/board.ts` (the `COLUMNS` or equivalent export). Not a functional concern for the prototype but means layout changes would need to be kept in sync by hand. *Open.*

**Problem 5: Google Fonts `@import` remains render-blocking.**

Identified in the previous session; unchanged. The `@import` at `PrototypeUI.vue:874` blocks rendering until the stylesheet is fetched from Google's CDN. Acceptable for throwaway prototype.

### Current state of the codebase

**Prototype (`frontend/src/views/PrototypeUI.vue`) — 890 lines.**

All three screens are fully rendered with mock data and the Artisan Tabletop styling. The connection-state dot logic is correct. The shuffle button works. The notification bar overlays without pushing content. The design brief accurately reflects all values.

Not yet implemented in the prototype:
- Tile placement interaction (selection is purely visual)
- Ghost tiles / pending placement highlighting on the board
- Blank-tile letter picker
- Swap-mode visual toggle (yellow tile tint)
- Submit/Clear/Pass/Forfeit button wiring (all are decorative)
- Theme picker dropdown
- Lobby form submission wiring

**Design brief (`docs/UI_DESIGN_BRIEF.md`) — rewritten, 340 lines.**

Now contains exact hex values, font stacks (EB Garamond, Work Sans, system-ui, SF Mono/JetBrains Mono), box-shadow strings, interaction states, and layout rules matching the prototype. Should be used as the implementation spec for production components.

**Backend and remaining frontend — unchanged from session 1.**

The route stubs, missing CORS middleware, and decorative prototype interactions documented in the previous session remain open. No new production code was written this session.

### References

| File | Key locations |
|------|---------------|
| `frontend/src/views/PrototypeUI.vue` | `colors` object (L14–34), `rackTiles` ref (L96–104), `shuffleRack()` (L109–117), `players` mock data (L121–124), opponent panel (L434–468), shuffle button (L602–631), current-player panel (L727–762), notification bar (L766–791), `pulse` keyframe (L886–889) |
| `docs/UI_DESIGN_BRIEF.md` | Full rewrite — palette (Visual Identity section), typography table, player panel spec (Screen 2 > Player Panel), notification bar spec (Screen 2 > Notification Bar), Design Principles (principles 6 and 8 added) |
