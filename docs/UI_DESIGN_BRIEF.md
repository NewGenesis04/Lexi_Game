# NEO Scrabble — UI Design Brief

## Product Overview

NEO Scrabble is a real-time multiplayer Scrabble web app. Two players, one board, turn-based. The frontend is a Vue 3 SPA driven entirely by server state pushed over SSE — the UI is "dumb," it only renders what the server says.

## Visual Identity

**Mood:** Premium, dark-first, depth-rich. Think luxury game set meets modern fintech dashboard. Gradients, shadows, glass morphism, and smooth animations create a tactile, immersive feel. Every surface has intentional depth.

**Theme reference (Dark — default):**

```
Board background:  neutral-800 (#262626)
Cell normal:       neutral-800
Cell DL:           blue-900
Cell TL:           blue-950
Cell DW:           rose-900
Cell TW:           red-950
Center star:       rose-900
Tile (occupied):   neutral-700 with glossy amber gradient
Tile letter:       white with subtle text shadow
Ghost tile:        green-700/800 with emerald-400 border, scale pulse
Border lines:      neutral-600
Page background:   neutral-900 (#171717)
Card/surface:      neutral-800/900 with backdrop blur
Text primary:      white
Text secondary:    neutral-400
Accent blue:       blue-600 (#2563eb)
Accent red:        red-700
Rack tile:         amber-100/200 gradient bg, neutral-900 text
```

Typography: System font stack (Inter or SF Pro), no custom typefaces. Headings bold and tight-tracked. UI labels in uppercase with wider letter-spacing. Buttons use bold, modern typography.

### Premium Design System

#### Depth & Layers
- Board: rounded corners (rounded-xl), `shadow-2xl` with dark drop shadow
- Cards: glass morphism — semi-transparent bg, `backdrop-blur-xl`, subtle border
- Tiles: glossy gradients with inner shadow illusion, `shadow-lg` per tile
- Interactive elements: `hover:scale-105` with `transition-all duration-200`

#### Gradients
- Board premium cells: subtle diagonal gradients per type (DL: blue, TL: deeper blue, DW: rose, TW: red)
- Occupied tiles: amber gradient (`from-amber-200 to-amber-100`)
- Rack background: amber gradient with `backdrop-blur`
- Action buttons: blue-600 with hover brightening
- Game over title: gradient text (`from-white via-blue-300 to-white`)
- Lobby title: rainbow gradient text

#### Glass Morphism
- Player panels: `bg-neutral-800/80 backdrop-blur-xl` with subtle border
- Notification bar: `bg-neutral-900/90 backdrop-blur-xl`
- Game over overlay: `bg-neutral-900/80 backdrop-blur-2xl`
- Lobby card: `bg-neutral-800/80 backdrop-blur-xl`

#### Shadows
- Board: `shadow-2xl` with `shadow-black/50`
- Tiles: `shadow-lg` with `shadow-black/30`
- Cards: `shadow-xl` with `shadow-black/40`
- Buttons: `shadow-md` with hover elevation
- Dropdowns: `shadow-2xl` with `shadow-black/60`

#### Animations
- Tile hover: `hover:scale-110 hover:-translate-y-1` with smooth transition
- Ghost tiles: subtle scale pulse (CSS keyframe)
- Button hover: `hover:scale-105` with brightness increase
- Notification entrance: slide from left
- Game overlay entrance: fade + scale
- Selection ring: smooth border transition

---

## Screen 1: Lobby (Create / Join)

A centered glass-morphism card on a neutral-900 page. No header. Just the card floating in dark space.

**Layout:**
- Centered card, max ~420px wide, `bg-neutral-800/80 backdrop-blur-xl` with subtle border, `rounded-2xl shadow-2xl`
- Title "NEO SCRABBLE" at top — large, bold, tracking-widest. Gradient text: `bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent`
- Two tab buttons below: "Create" | "Join" — pill-style, active tab has gradient fill (`from-blue-600 to-blue-700`), inactive is muted outline with `hover:bg-neutral-700/50`
- Form fields below the active tab, vertically stacked with generous gap
- Create tab: nickname input (enhanced with `ring-1 ring-neutral-600 focus:ring-2 focus:ring-blue-500` and `bg-neutral-700/50`), dictionary dropdown, time limit dropdown, submit button (full-width, gradient `from-blue-600 to-blue-700`, `shadow-lg`, `hover:scale-[1.02]`)
- Join tab: game code input (6-char, centered text, monospace, larger font), nickname input, submit button (green gradient `from-emerald-600 to-green-700`)
- Submit buttons say "Creating…" / "Joining…" with a subtle spinner when loading, disabled state dims with `opacity-60`
- No decorative elements. Pure typography, spacing, and material depth.

**States:**
- Error: inline red text below the form with subtle shake, or the global notification bar at the bottom
- Loading: button shows spinner, fields disabled with reduced opacity
- Empty: just the card, waiting for user input

---

## Screen 2: Game Board (Main Play Screen)

This is the core screen. It must feel like a premium physical board game — depth, gloss, and tactile feedback.

**Overall Layout:**

```
┌──────────────────────────────────────────────────┐
│ Header                        Theme  Leave        │
├──────────────────────────────────────────────────┤
│                                                   │
│   ┌──────┐          ┌──────────┐    ┌──────┐     │
│   │Player│          │  BOARD   │    │Player│     │
│   │Panel │          │  15×15   │    │Panel │     │
│   │(opp) │          │ premium  │    │(you) │     │
│   └──────┘          │ squares  │    └──────┘     │
│                     │ visible  │                   │
│                     └──────────┘                   │
│                     ┌──────────┐                   │
│                     │ TILE     │                   │
│                     │ TRAY     │                   │
│                     │ (rack)   │                   │
│                     └──────────┘                   │
│                     ┌──────────┐                   │
│                     │ CONTROLS │                   │
│                     │ (buttons)│                   │
│                     └──────────┘                   │
│                                                   │
├──────────────────────────────────────────────────┤
│  Notification Feed (chats, game events, errors)   │
└──────────────────────────────────────────────────┘
```

On wide screens: board is centered, player panels flank left/right.
On narrow screens: player panels go top/bottom, everything stacks vertically.

### Header
- Left: game code in monospace, muted
- Right: "Theme" text button (opens the theme swatch dropdown with glass morphism panel), "Leave" red button (gradient `from-red-700 to-red-800`)

### Player Panel (×2 — opponent top/left, you bottom/right)
A compact card, ~180px wide, glass morphism:
- `bg-neutral-800/60 backdrop-blur-xl rounded-xl border border-neutral-700/50 shadow-xl`
- Name (semibold, white, `tracking-wide`)
- Score (extra-large, bold, gradient text `from-blue-400 to-blue-300 bg-clip-text text-transparent`)
- Time remaining (monospace, muted: "5:32" format)
- Connection indicator: green glowing dot (`ring-2 ring-green-500/50 ring-offset-2 ring-offset-neutral-900`) if connected, red if disconnected, gray if waiting
- "● Your Turn" / "● Their Turn" badge: `bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full px-3 py-0.5 text-xs font-semibold`

### Board (15×15 Grid)
- The board is the visual anchor. `rounded-2xl shadow-2xl shadow-black/50 border-2 border-neutral-600 p-1`
- Cells are 36×36px on desktop (labelled with row numbers 1–15 and column letters A–O on all four sides)
- Premium squares show their label (DL, TL, DW, TW, ★) in muted colored text when empty, with soft gradient backgrounds:
  - DL: `bg-gradient-to-br from-blue-900 to-blue-950` with `text-blue-300`
  - TL: `bg-gradient-to-br from-blue-950 to-indigo-950` with `text-blue-400`
  - DW: `bg-gradient-to-br from-rose-900 to-rose-950` with `text-rose-300`
  - TW: `bg-gradient-to-br from-red-950 to-rose-950` with `text-red-400`
  - ★: `bg-gradient-to-br from-rose-900 to-rose-950` with `text-rose-300`
- When a tile is placed: glossy tile appearance with gradient `from-amber-200 to-amber-100`, bold white letter with subtle `text-shadow`, small point value displayed bottom-right in tiny muted text
- Ghost tiles (pending placement): `bg-gradient-to-br from-emerald-800 to-green-700` with `border-2 border-emerald-400`, `shadow-lg shadow-emerald-900/50`, subtle scale animation, letter in white
- Tile appearance: `rounded-md shadow-lg shadow-black/30` with glossy finish
- Hover effects on empty cells when a rack tile is selected: `hover:brightness-125 hover:scale-105 transition-all`
- Point value displayed as subscript on placed tiles (e.g., "A₁")

### Tile Tray (Rack)
- A sleek horizontal strip below the board, `bg-gradient-to-r from-amber-900/30 via-amber-800/20 to-amber-900/30 backdrop-blur-xl rounded-xl p-1 shadow-lg`
- 7 tile slots, each tile is 42×42px, glossy 3D appearance:
  - `bg-gradient-to-br from-amber-200 to-amber-100` with `shadow-lg shadow-black/30 rounded-lg`
  - Letter in bold `text-neutral-900`, large (`text-lg`)
  - `hover:scale-110 hover:-translate-y-2 transition-all duration-200 cursor-pointer`
- Selected tile: `ring-2 ring-blue-400 ring-offset-2 ring-offset-amber-100 -translate-y-3 scale-110`
- Swap-marked tile: `bg-gradient-to-br from-yellow-400 to-amber-400 scale-110 ring-2 ring-yellow-300`
- Ghost-used tile (already placed on board): `opacity-40 scale-90 pointer-events-none`
- Blanks show "?" as the letter
- Empty rack shows placeholder text centered in the strip

### Controls (below tile tray)
A horizontal row of buttons, compact, all same height (~34px), `gap-2`:
- **Submit** — gradient `from-blue-600 to-blue-700`, `shadow-md`, `hover:shadow-lg hover:scale-105`, appears only when tiles are placed or swap-selected, says "Submit" or "Swap" contextually
- **Clear** — `bg-neutral-700/80 hover:bg-neutral-600`, appears only when ghost tiles exist
- **Swap** — `bg-neutral-700/80 hover:bg-neutral-600`, toggles swap mode (yellow tint when active: `bg-yellow-700`)
- **Pass** — `bg-neutral-700/80 hover:bg-neutral-600`
- **Forfeit** — gradient `from-red-700 to-red-800`, `hover:scale-105`

Consider hiding Pass/Forfeit behind a dotted "⋯" meatball menu to keep the main row clean. The Submit button should be the most visually prominent.

### Interaction States
- Resting: all controls visible but muted
- Placing tiles: tile in rack is selected (blue ring with lift), empty board cells are hoverable (scale + brightness), placing creates a ghost tile with emerald glow
- Swap mode: swap button highlighted yellow, clicking rack tiles marks them for exchange with yellow gradient
- Blank tile placed: a floating 26-letter grid picker appears near the tile with glass morphism, selecting a letter assigns it with a snap transition
- Submitting: button shows "Submitting…", all inputs locked with dimmed opacity

---

## Screen 3: Game Over

When `game.phase === 'finished'`, the board remains visible but a centered overlay appears (`bg-neutral-900/80 backdrop-blur-2xl`).

**Overlay card:**
- Centered, `bg-neutral-800/90 backdrop-blur-xl rounded-2xl border border-neutral-700/50 shadow-2xl shadow-black/50`, padding generous
- "GAME OVER" in all-caps, extra-bold, tracking-widest. Gradient text: `bg-gradient-to-r from-white via-blue-300 to-white bg-clip-text text-transparent`
- Winner name + final score: large, bold, gradient `from-yellow-400 to-amber-300`
- "Final scores:" with both players' names and scores listed. Each score in its own glass card: `bg-neutral-700/50 backdrop-blur-sm rounded-lg border border-neutral-600/30`
- "Play Again" button (gradient `from-blue-600 to-blue-700`, `shadow-lg`, `hover:scale-105`)
- Tiles on the board stay in place beneath the overlay (faded but visible)
- Entrance animation: `animate-fadeIn` with slight scale

If a tie: "DRAW — No winner" in gradient text instead of a winner name.

---

## Persistent UI: Notification Bar (Bottom)

A fixed bar at the very bottom of the screen, spanning full width, ~56px tall.

- `bg-neutral-900/90 backdrop-blur-xl border-t border-neutral-700/50 shadow-2xl shadow-black/30`
- Notifications slide in from the left edge of this bar with `transition-all duration-500`
- Each notification is a short text message with an icon/color: error (red), info (neutral), success (green)
- Notifications auto-dismiss after 5 seconds with a smooth fade
- Chats from opponent appear here too (future feature)
- The bar is always visible but empty when no notifications exist (small empty state dot or just empty)

Example messages:
- "Game not found — redirected to lobby" (error, red)
- "Opponent played STARE for 24 points" (info, neutral)
- "You played STAR for 12 points" (info, neutral)
- "Connected" (success, green)
- "Opponent disconnected — game paused" (warning, yellow)

---

## Persistent UI: Settings Panel

Triggered by clicking "Theme" in the header. Opens as a small dropdown panel from the header with glass morphism.

**Theme Picker (existing):**
- 3-column grid of color swatches in a `bg-neutral-800/90 backdrop-blur-xl rounded-xl border border-neutral-700/50 shadow-2xl` panel
- Each swatch is a 48×32px rectangle showing the board bg with a 2px border, `rounded-lg`
- Active theme has a blue-500 ring with `shadow-md`
- Theme name below each swatch in tiny text
- Clicking applies immediately with a smooth transition

**Future settings (placeholder):**
- Dictionary toggle
- Time limit
- Sound on/off
- These are grayed out with "Coming soon" label

---

## Design Principles

1. **The board is king.** Everything else is chrome. The board should feel like a premium physical object on a dark felt table — depth, shadow, and gloss make it tangible.
2. **One action per tap.** Never ask the user to confirm. Submit sends immediately. Swap sends immediately. Clear is instant.
3. **Silence is the interface.** Empty states are just dark space. No spinners unless loading. No toasts unless something happened.
4. **Notifications are a ticker, not a popup.** They live in the bottom bar. They don't interrupt. They don't block.
5. **Premium squares whisper.** The board tells you where you are through color and subtle gradients, not through labels screaming at you.
6. **Dark by default, light optional.** The "Dark" theme is the default. Themes remain available for those who want them but the premium gradient system is designed for the dark theme.
7. **Depth serves clarity.** Shadows, gradients, and glass effects are not decoration — they create hierarchy and guide the eye to the board and tiles.
