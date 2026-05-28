# NEO Scrabble — UI Design Brief

## Product Overview

NEO Scrabble is a real-time multiplayer Scrabble web app. Two players, one board, turn-based. The frontend is a Vue 3 SPA driven entirely by server state pushed over SSE — the UI is "dumb," it only renders what the server says.

---

## Visual Identity

**Mood:** Premium, dark-first, warm-toned. Think artisan tabletop craft meets modern fintech dashboard. The palette is built around brass, walnut, and copper with deep shadows and subtle glass/inset effects. Every surface has intentional depth.

**Typography — layered approach:**

| Context | Font | Weight(s) | Notes |
|---------|------|-----------|-------|
| Page body / board letters / headings | **EB Garamond** (serif) | 400, 500, 600 | Primary personality — warm, literary |
| UI labels / buttons / table headers | **Work Sans** (sans-serif) | 700, 600 | UP100, 0.1em tracking |
| Player panel name / score / labels | **System UI stack** (`system-ui, -apple-system, sans-serif`) | 700 / 900 | Panels match Bloomberg-standard spec |
| Clock readout | **SF Mono / JetBrains Mono** (monospace) | 700 | `tabular-nums` for stable alignment |

**Palette reference ("Artisan Tabletop" — the only theme in the prototype):**

| Token | Hex | Usage |
|-------|-----|-------|
| `surface` | `#131313` | Page background |
| `surface-container-lowest` | `#0e0e0e` | Deepest surface |
| `surface-container-low` | `#1b1c1c` | Header, board inset |
| `surfaceContainer` | `#202020` | Mid container |
| `surface-container-high` | `#2a2a2a` | Tile rack default |
| `surface-container-highest` | `#353535` | Rack hover |
| `onSurface` | `#e5e2e1` | Primary text |
| `on-surface-variant` | `#d3c3c0` | Secondary text |
| `outline` | `#9c8d8b` | Brass border |
| `outline-variant` | `#504442` | Subtle border |
| `primary` | `#e3beb8` | Brass/copper accent |
| `on-primary` | `#422a26` | Text on primary |
| `primary-container` | `#3e2723` | Dark walnut (DW cells, lobby bg) |
| `secondary` | `#d6c3bc` | Neutral accent |
| `tertiary` | `#ffb5a0` | Alert/forfeit accent |
| `tertiary-container` | `#5a1200` | Forfeit button bg |
| `primary-fixed-dim` | `#e3beb8` | Rack selected gradient |
| Board DL bg | `#1e405a` | Cool blue |
| Board DL label | `#7ab8d4` | Light blue |
| Board TL bg | `#0e2433` | Dark blue |
| Board TL label | `#5a9ec4` | Mid blue |
| Board DW / ★ bg | `primary-container` (`#3e2723`) | Dark walnut |
| Board DW / ★ label | `primary-fixed-dim` (`#e3beb8`) | Brass |
| Board TW bg | `#3d1414` | Dark crimson |
| Board TW label | `#d47a7a` | Light red |
| Placed tile bg | `#d4c5a9` | Warm beige |
| Placed tile letter | `#1a1a1a` | Near-black |

---

### Premium Design System

#### Depth & Layers
- **Board container:** 2px brass border (`colors.outline`), `linear-gradient(180deg, #131313 → #1b1c1c)` bg, `0 6px 24px rgba(0,0,0,0.6)` drop shadow + `inset 0 1px 0 rgba(255,255,255,0.06)` highlight
- **Board cells:** `1px` solid border, `inset 0 1px 2px rgba(0,0,0,0.3)` shadow, `box-sizing: border-box`
- **Placed tiles:** `0 2px 6px rgba(0,0,0,0.5)` drop shadow, warm beige bg with dark lettering + light text-shadow
- **Rack tiles:** Overshoot cubic-bezier hover lift (`translateY(-3px) scale(1.06)`), selected lifted further (`-6px`) with primary ring
- **Player panels:** Semi-transparent `rgba(38,38,38,0.4)` bg, subtle `rgba(96,96,96,0.3)` border, separated into vertical blocks
- **Cards/Cards:** Glass morphism via semi-transparent bg on dark, subtle border

#### Premium Square Colours
Premium squares do NOT use gradients. Each type gets a solid deep background with a contrasting muted label:

| Square | Background | Label Colour |
|--------|-----------|-------------|
| DL (×2 letter) | `#1e405a` (cool navy) | `#7ab8d4` (light blue) |
| TL (×3 letter) | `#0e2433` (deep navy) | `#5a9ec4` (mid blue) |
| DW (×2 word) | `#3e2723` (dark walnut) | `#e3beb8` (brass) |
| TW (×3 word) | `#3d1414` (dark crimson) | `#d47a7a` (light red) |
| ★ (center) | `#3e2723` (dark walnut) | `#e3beb8` (brass) |

Labels rendered in Work Sans, 8px, 700 weight, 0.1em tracking.

#### Gradients
- Board container: subtle diagonal/vertical from `surface-dim` to `surface-container-low`
- Rack tiles: `linear-gradient(180deg, surface-container-high → surfaceContainer)` default, primary gradient when selected
- Action buttons: `linear-gradient(180deg, outline → #8a7d7b)` for submit/create/join
- Rack background: `linear-gradient(180deg, surface-container-low → surfaceContainer)`

#### Shadows
- Board container: `0 6px 24px rgba(0,0,0,0.6)` + `inset 0 1px 0 rgba(255,255,255,0.06)`
- Cells: `inset 0 1px 2px rgba(0,0,0,0.3)` (empty), `0 2px 6px rgba(0,0,0,0.5)` (occupied)
- Rack tiles: `0 1px 3px rgba(0,0,0,0.4)` + `inset 0 1px 0 rgba(255,255,255,0.08)` (default); `0 4px 12px` (hovered); `0 2px 8px` + `0 0 0 1px primary` (selected)
- Player panels: none (only the thin border)
- Buttons: `0 2px 4px rgba(0,0,0,0.4)` + `inset 0 1px 0 rgba(255,255,255,0.15)` for filled; none for outlined
- Card/lobby: `0 2px 8px rgba(0,0,0,0.5)`

#### Animations
- Rack tile hover: `translateY(-3px) scale(1.06)` with `cubic-bezier(0.34, 1.56, 0.64, 1)`, 200ms
- Rack tile selected: `translateY(-6px)` same curve
- Notification bar: `slideUp` keyframe (translateY 100%→0 + opacity), 250ms
- Game over overlay: `fadeIn` (opacity 0→1 + scale 0.95→1), 400ms
- Connection dot: `pulse` keyframe (opacity 1→0.4→1, 2s infinite) for connected-but-not-turn

---

## Screen 1: Lobby (Create / Join)

A centered card on a `#131313` page with no header. Just the card floating in dark space.

**Layout:**
- Centered card, max `400px` wide, `background: #3e2723` (primary-container), `1px solid #9c8d8b` (outline) border, `0 2px 8px rgba(0,0,0,0.5)`, `rounded-lg`, padding 32px
- Title "NEO SCRABBLE" — EB Garamond, 32px, 500 weight, `color: #e3beb8` (primary), centered
- Two tab buttons below in a segmented control: `background: #0e0e0e` (surface-container-lowest), 2px padding
  - Active tab: `background: #9c8d8b` (outline), text `#0e0e0e`, Work Sans, 700, 0.1em tracking, uppercase
  - Inactive tab: transparent bg, text `#d3c3c0` (on-surface-variant)
- Form fields inside the active tab vertically stacked with generous gap
  - Inputs: `background: #0e0e0e`, `1px solid #504442` border, `inset 0 2px 4px rgba(0,0,0,0.5)` shadow, EB Garamond 18px or Work Sans 12px
  - Selects: same styling as inputs
  - Submit button: `linear-gradient(180deg, #9c8d8b → #8a7d7b)`, text `#0e0e0e`, Work Sans 12px 700, 0.1em tracking, `0 2px 4px rgba(0,0,0,0.4)` + `inset 0 1px 0 rgba(255,255,255,0.15)`, full-width
- No decorative elements. Pure typography, spacing, and material depth.

---

## Screen 2: Game Board (Main Play Screen)

The core screen. Must feel like a premium physical board game — depth, gloss, and tactile feedback.

**Overall Layout:**

```
┌──────────────────────────────────────────────────────┐
│ Header                          Theme    Leave        │
├──────────────────────────────────────────────────────┤
│                                                        │
│   ┌──────┐               ┌──────────┐   ┌──────┐      │
│   │Player│     Bag(◉)    │  BOARD   │   │Player│      │
│   │Panel │               │  15×15   │   │Panel │      │
│   │(opp) │               │ premium  │   │(you) │      │
│   └──────┘               │ squares  │   └──────┘      │
│                          │ visible  │                  │
│                          └──────────┘                  │
│                          ┌──────────┐                  │
│                          │ TILE     │                  │
│                          │ TRAY     │                  │
│                          │ (rack)  ⇄│  (shuffle btn)   │
│                          └──────────┘                  │
│                          ┌──────────┐                  │
│                          │ CONTROLS │                  │
│                          │ (buttons)│                  │
│                          └──────────┘                  │
│                                                        │
├────────────────────────────────────────────────────────┤
│              Notification Bar (fixed overlay)           │
└────────────────────────────────────────────────────────┘
```

On wide screens (lg+): board centered, player panels flank left/right in `flex-row`.
On narrow screens: everything stacks vertically in `flex-col`, panels go top/bottom.

### Header
- Left: "GAME · XY7K9M" — Work Sans, 12px, 700, 0.1em tracking, `color: #d3c3c0` (on-surface-variant)
- Right:
  - "Theme" text button — Work Sans 12px 700, `color: #d6c3bc` (secondary), `1px solid #9c8d8b` outline, transparent bg, hover fills to `#2a2a2a`
  - "Leave" — Work Sans 12px 700, `background: #5a1200` (tertiary-container), text `#ffb5a0` (tertiary), `0 2px 4px rgba(0,0,0,0.3)`, hover dims

### Player Panel (×2 — opponent left/top, you right/bottom)
A compact card, `w-44` (176px), with the following structure:

```
┌─────────────────────────────┐  ← emerald 2px top border if active turn
│  ● Player Name              │     otherwise 1px standard border
│─────────────────────────────│
│                             │
│          137                │  ← 36px, 900 weight, tabular-nums
│                             │
│─────────────────────────────│
│  TIME              5:42     │  ← micro label 9px / mono 15px
└─────────────────────────────┘
```

- `background: rgba(38,38,38,0.4)`
- `border: 1px solid rgba(96,96,96,0.3)`
- Active turn: `borderTop: 2px solid #10b981` (emerald)
- Inactive/disconnected: `opacity: 0.5` (disconnected only)
- System font stack throughout (`system-ui, -apple-system, sans-serif`)
- Separator lines: `1px solid rgba(96,96,96,0.2)`
- Connection dot: 6px circle
  - **Green** (`#10b981`) + glow: active turn + connected
  - **Pulsing emerald** (`#34d399`) + pulsing: connected but not turn
  - **Muted gray** + no glow: disconnected
- Name: 14px, 700 weight, `#e5e5e5`, `-0.02em` tracking
- Score: 36px, 900 weight, white, `-0.03em` tracking, `font-variant-numeric: tabular-nums`
- "TIME" label: 9px, 900 weight, `#6b7280`, `0.15em` tracking
- Clock: SF Mono / JetBrains Mono, 15px, 700 weight, `#a3a3a3` (`#ffb5a0` when < 60s)

### Bag Indicator
A standalone pill badge positioned above the board:
- `background: rgba(38,38,38,0.4)`, `border-radius: 999px`, `border: 1px solid rgba(96,96,96,0.3)`
- Contains `bag.svg` icon (16×16) + remaining tile count in system font 12px 700

### Board (15×15 Grid)
The visual anchor.
- **Container:** `border-radius: 0.625rem`, `border: 2px solid #9c8d8b`, `background: linear-gradient(180deg, #131313 → #1b1c1c)`, `box-shadow: 0 6px 24px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)`, padding 8px
- **Cells:** 36×36px (w-9 h-9), each wrapped in a 1px padding cell (`p-[1px]`)
  - `box-sizing: border-box` on the inner cell div
  - `border: 1px solid ...` (outline-variant for empty, outline for occupied)
  - `border-radius: 0.125rem`
  - Empty cells: `inset 0 1px 2px rgba(0,0,0,0.3)` shadow
  - Occupied cells: `0 2px 6px rgba(0,0,0,0.5)` shadow
- **Premium labels:** Work Sans 8px 700, shown only when cell is empty
- **Placed tiles:** warm beige (`#d4c5a9`) bg, EB Garamond 18px 600 letter in `#1a1a1a` with `0 1px 0 rgba(255,255,255,0.3)` text-shadow, points in Work Sans 8px at bottom-right in `#5a4a3a`
- **Labels:** Row numbers (1–15) and column letters (A–O) on all four sides in Work Sans 12px 700

### Tile Tray (Rack)
A sleek horizontal strip below the board:
- `background: linear-gradient(180deg, #1b1c1c → #202020)`, `border-radius: 0.375rem`, `border: 1px solid #504442`, `inset 0 1px 2px rgba(0,0,0,0.3)`, padding 6px
- 7 tile slots + 1 shuffle button, flex row with 6px gap
- Each tile: 44×44px
  - Default: `linear-gradient(180deg, #2a2a2a → #202020)`, `1px solid #504442`, `0 1px 3px rgba(0,0,0,0.4)` + `inset 0 1px 0 rgba(255,255,255,0.08)`
  - Hovered: `translateY(-3px) scale(1.06)`, gradient `#353535 → #2a2a2a`, `0 4px 12px rgba(0,0,0,0.5)` + `inset 0 1px 0 rgba(255,255,255,0.12)`
  - Selected: `translateY(-6px)`, gradient `#e3beb8 → #e3beb8`, emerald ring `0 0 0 1px #e3beb8`, `0 2px 8px rgba(0,0,0,0.5)` + `inset 0 1px 0 rgba(255,255,255,0.15)`, border becomes `#e3beb8`
  - Transition: `all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)` (overshoot spring)
- Letter: EB Garamond, 20px, 600 weight; default `#d3c3c0` with `0 1px 2px rgba(0,0,0,0.5)` text-shadow; selected `#422a26` (on-primary)
- Points: Work Sans, 8px, 600; default `#9c8d8b`; selected `#422a26`
- **Shuffle button:** 36×36px, transparent bg, `1px solid #504442` border, `border-radius: 0.375rem`, cross-arrows SVG icon in `#9c8d8b`, hover dims to 70% opacity

### Controls (below tile rack)
A horizontal row of 5 buttons, `gap-2`, `items-center justify-center`:
- **Submit** — `linear-gradient(180deg, #9c8d8b → #8a7d7b)`, text `#0e0e0e`, `0 2px 4px rgba(0,0,0,0.4)` + `inset 0 1px 0 rgba(255,255,255,0.15)`, `border-radius: 0.25rem`, padding 8px 20px, Work Sans 12px 700, hover dims
- **Clear / Swap / Pass** — transparent bg, `1px solid #504442`, text `#d3c3c0`, padding 8px 16px, hover fills to `#2a2a2a`
- **Forfeit** — `background: #5a1200`, text `#ffb5a0`, `1px solid #ffb5a0`, `0 2px 4px rgba(0,0,0,0.3)`, hover dims

---

## Screen 3: Game Over

When game phase is 'finished', the board remains visible but a centered overlay appears.

**Overlay card:**
- `background: rgba(19,19,19,0.9)`, full-screen fixed, flex centered
- Card: `background: #1b1c1c` (surface-container-low), `border-radius: 0.5rem`, `border: 1px solid #9c8d8b`, `0 4px 24px rgba(0,0,0,0.6)`, padding 32px, max-width 360px
- "GAME OVER" — EB Garamond 32px 600, `color: #d3c3c0`
- Winner name — EB Garamond 28px 500, `color: #e3beb8` (primary)
- Winner score — Work Sans 36px 600, `color: #e5e2e1`
- Final scores section:
  - Each player row: `background: #202020` (surfaceContainer), `1px solid #504442`, `border-radius: 0.375rem`, flex row with name (EB Garamond 18px) and score (Work Sans 24px 600)
  - Winner score: `color: #e3beb8` | Loser score: `color: #ffb5a0`
- "Play Again" button — same gradient brass style as Submit

---

## Notification Bar (Fixed Overlay)

A fixed bar at the very bottom of the screen, spanning full width, ~30px tall.
- `background: #1b1c1c` (surface-container-low), `border-top: 1px solid #504442` (outline-variant)
- `fixed bottom-0 left-0 right-0 z-50`
- Appears with `slideUp` animation (250ms, translateY 100% → 0)
- Auto-cycles through 3 notification types every 3.5s:
  1. Self-move: "**You** played **STARE** +24" (dot: `#e3beb8`)
  2. Opponent-move: "**Jax** played **QUITE** +18" (dot: `#d6c3bc`)
  3. Connected: "**Jax** connected" (dot: `#4caf50`)
- Click to dismiss
- Hidden when no notification is active
- Text: system font 12px, `color: #d3c3c0` with bold user names in `#e5e2e1`
- Does NOT push content — overlays as fixed layer

---

## Persistent UI: Settings Panel

(The prototype has a "Theme" button in the header but no dropdown panel yet — placeholder for future.)

---

## Design Principles

1. **The board is king.** Everything else is chrome. The board should feel like a premium physical object on a dark felt table — depth, shadow, and gloss make it tangible.
2. **One action per tap.** Never ask the user to confirm. Submit sends immediately. Clear is instant.
3. **Silence is the interface.** Empty states are just dark space. No spinners unless loading. No toasts unless something happened.
4. **Notifications are a ticker, not a popup.** They live in a slim fixed bar at the bottom. 30px, auto-dismiss, click to dismiss. They don't interrupt.
5. **Premium squares whisper.** The board tells you where you are through colour and subtle labels, not through screaming bright badges.
6. **Warmth over coldness.** The palette uses warm brass, walnut, and copper tones rather than cool blues/greys. This creates a tactile, physical-game feel.
7. **Depth serves clarity.** Shadows, gradients, and inset effects are not decoration — they create hierarchy and guide the eye to the board and tiles.
8. **Connection state is explicit.** Green = your turn, pulsing emerald = connected (waiting), gray = disconnected. Tells the player exactly what's happening.
