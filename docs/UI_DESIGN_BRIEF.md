# LEXI — Neo-Brutalist UI Design Brief

## Product Overview

NEO Scrabble is a real-time multiplayer Scrabble web app. Two players, one board, turn-based. The frontend is a Vue 3 SPA driven entirely by server state pushed over SSE — the UI is "dumb," it only renders what the server says.

The design language is **Lexi**: a neo-brutalist system with hard offset shadows (no blur), 2px solid borders, monospace UI text, and full light/dark mode support. Paper meets punch.

---

## Visual Identity

**Mood:** Neo-brutalist, tactile, unapologetically physical. Shadows are hard offsets — 3px, 4px, 6px — never blurred. Borders are always 2px solid. Surfaces feel stamped rather than floated. Light mode evokes cream paper and ink; dark mode feels like a chalkboard in a dim room.

**Typography — layered approach:**

| Context | Font | Weight(s) | Notes |
|---------|------|-----------|-------|
| Page / section titles, board letters | **EB Garamond** (serif) | 400–600 | `font-lexi-display` |
| All UI labels, buttons, table headers | **Space Mono** (monospace) | 700 | `font-lexi-ui`, `tracking-lexi-ui` (0.08em) |
| Scores, clocks, numeric data | **Space Mono** (monospace) | 700, 900 | `font-lexi-numeric`, `tabular-nums` |

No sans-serif anywhere in the system. Space Mono is the single voice for all chrome.

---

### Palette — Light Mode (`[data-theme="light"]`)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#F5F0E4` | Page background |
| `--color-bg-elevated` | `#FAF7F0` | Cards, panels, modals |
| `--color-bg-sunken` | `#EDE4D0` | Rack, board inset, inputs |
| `--color-text-primary` | `#0F0F0F` | Body copy, headings |
| `--color-text-secondary` | `#555555` | Labels, captions |
| `--color-text-muted` | `#777777` | Hints, placeholders |
| `--color-primary` | `#F5CC42` | Acid Yellow — brand accent, selected tiles |
| `--color-secondary` | `#2D64D4` | Cobalt Blue |
| `--color-danger` | `#D42B14` | Brick Red |
| `--color-success` | `#1F8040` | Forest Green |
| `--color-warning` | `#C85520` | Terracotta |
| `--color-border` | `#0F0F0F` | Black ink — default border |
| `--color-border-subtle` | `#555555` | Subtle border |
| `--color-border-muted` | `#AAAAAA` | Muted border |

### Palette — Dark Mode (`[data-theme="dark"]`)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#1A1A1A` | Page background |
| `--color-bg-elevated` | `#252525` | Cards, panels, modals |
| `--color-bg-sunken` | `#0F0F0F` | Rack, board inset, inputs |
| `--color-text-primary` | `#E5E5E5` | Body copy, headings |
| `--color-text-secondary` | `#AAAAAA` | Labels, captions |
| `--color-text-muted` | `#777777` | Hints, placeholders |
| `--color-primary` | `#687A40` | Dusty Olive — brand accent, selected tiles |
| `--color-secondary` | `#5A7294` | Muted Slate |
| `--color-danger` | `#E85A44` | Muted Brick |
| `--color-success` | `#3CAF64` | Muted Forest |
| `--color-warning` | `#A88C80` | Muted Terracotta |
| `--color-border` | `#E5E5E5` | Near-white — default border |
| `--color-border-subtle` | `#AAAAAA` | Subtle border |
| `--color-border-muted` | `#555555` | Muted border |

### Invariant Tokens (same in both modes)

**Shadows (no blur — the brutalist signature):**

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-lexi-sm` | `3px 3px 0px var(--color-border)` | Buttons, small tiles |
| `shadow-lexi-md` | `4px 4px 0px var(--color-border)` | Cards, panels |
| `shadow-lexi-lg` | `6px 6px 0px var(--color-border)` | Board container, modals |
| `shadow-lexi-pressed` | `1px 1px 0px var(--color-border)` | Active/pressed state |
| `shadow-lexi-tile-hover` | `6px 8px 0px var(--color-border)` | Rack tile hover |
| `shadow-lexi-tile-selected` | `6px 10px 0px var(--color-border)` | Rack tile selected |

**Border radius:**

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-lexi-xs` | `2px` | Tiles, board cells |
| `rounded-lexi-sm` | `4px` | Buttons, inputs, badges |
| Cards, board container | `0px` | Brutalist — no radius |

---

### Premium Board Squares

Board squares use flat fills with high label contrast. No gradients.

| Square | Light bg | Light label | Dark bg | Dark label |
|--------|----------|-------------|---------|------------|
| DL (×2 letter) | `#C2D9FA` (cobalt-200) | `#1A3A6E` (cobalt-700) | `#1C2535` (slate-700) | `#B8CCE0` (slate-200) |
| TL (×3 letter) | `#F8CEB8` (terra-200) | `#6B2A10` (terra-700) | `#2A1810` (mterra-700) | `#CEB8B0` (mterra-200) |
| DW (×2 word) | `#B8EDD0` (forest-200) | `#0D3D1A` (forest-700) | `#0D3D1A` (forest-700) | `#B8EDD0` (forest-200) |
| TW (×3 word) | `#FAC4BC` (brick-200) | `#7A1A0A` (brick-700) | `#7A1A0A` (brick-700) | `#F49080` (brick-300) |
| ★ (center) | `#FAE080` (yellow-300) | `#0F0F0F` (ink-900) | `#1E2410` (olive-700) | `#E4EDD4` (olive-100) |

Labels in Space Mono, 10px, 700 weight, 0.12em tracking. Shown only when cell is empty.

---

### The Neo-Brutalist Signature

Every interactive element follows the same physical metaphor:

| State | Shadow | Transform | Transition |
|-------|--------|-----------|------------|
| Default | `shadow-lexi-md` | none | — |
| Hover | `shadow-lexi-lg` | `translate(-1px, -1px)` | `150ms ease` |
| Active | `shadow-lexi-pressed` | `translate(2px, 2px)` | immediate |

Rack tiles use an overshoot spring: `cubic-bezier(0.34, 1.20, 0.64, 1)`, 200ms.
Default → hover lifts `(-2px, -4px)`. Selected lifts further `(-2px, -6px)`.

---

## Screen 1: Lobby (Create / Join)

A centered card on page background with no header. Just the card floating in dark/light space.

**Layout:**
- Centered card, max `384px` wide, `bg-lexi-bg-elevated`, `border-lexi border-lexi-border`, `shadow-lexi-lg`, padding 32px
- Title "LEXI" — Space Mono, 32px, 700 weight, uppercase, 0.12em tracking, centered
- **Avatar picker** — 5-column grid, 10 Multiavatar PNGs. Selected avatar: `border-lexi border-lexi-primary shadow-lexi-sm -translate-x-px -translate-y-px`. Unselected: `border-lexi-light border-lexi-border-muted`. Randomly assigned on mount.
- **Tab switcher** — Two buttons (CREATE / JOIN) side by side, separated by a 2px black border. Active tab: `bg-lexi-primary text-lexi-text-on-accent`. Inactive: transparent bg, secondary text.
- **Form fields** vertically stacked with 16px gap:
  - Inputs: `bg-lexi-bg-sunken`, `border-lexi border-lexi-border`, `shadow-lexi-sm`, Space Mono 14px, placeholder text in muted color, `focus:shadow-lexi-md focus:-translate-x-px focus:-translate-y-px`
  - Selects: same styling as inputs
  - Submit button: `bg-lexi-primary text-lexi-text-on-accent`, `border-lexi border-lexi-border`, `shadow-lexi-md`, full-width, Space Mono 12px 700 uppercase 0.12em tracking. Hover: `shadow-lexi-lg -translate-x-px -translate-y-px`. Active: `shadow-lexi-pressed translate-x-0.5 translate-y-0.5`. Disabled: `opacity-40`
- **Theme toggle** — Absolute top-right corner, 36×36px, `border-lexi border-lexi-border shadow-lexi-sm`, sun/moon SVG. Toggles between light and dark.
- Error text: `text-lexi-danger`, Space Mono 10px, centered below form.

---

## Screen 2: Game Board (Main Play Screen)

The core screen. Neo-brutalist physicality — the board feels like a stamped object on a textured surface.

**Overall Layout:**

```
┌──────────────────────────────────────────────────────┐
│ Header (code COPY)          ☀ HISTORY  LEAVE          │
├──────────────────────────────────────────────────────┤
│                                                        │
│   ┌──────┐  ┌───┐  ┌──────────┐   ┌──────┐           │
│   │Player│  │Bag│  │  BOARD   │   │Player│           │
│   │Panel │  │◉  │  │  15×15   │   │Panel │           │
│   │(opp) │  └───┘  │ premium  │   │(you) │           │
│   └──────┘         │ squares  │   └──────┘           │
│                    │ visible  │                        │
│                    └──────────┘                        │
│                    ┌──────────┐                        │
│                    │ TILE     │                        │
│                    │ TRAY     │                        │
│                    │ (rack)  ⇄│  (shuffle btn)        │
│                    └──────────┘                        │
│                    ┌──────────┐                        │
│                    │ CONTROLS │                        │
│                    │ (buttons)│                        │
│                    └──────────┘                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│              Notification Bar (fixed overlay)           │
└────────────────────────────────────────────────────────┘
```

On wide screens (lg+): board centered, player panels flank left/right.
On narrow screens: everything stacks vertically.

### Header

- **Left:** "GAME · XY7K9M" — clickable, copies code to clipboard. Space Mono 11px, 700, 0.12em tracking, secondary text. Copy icon (12px SVG) next to label.
- **Right (L→R):**
  - **Theme toggle** — sun/moon SVG icon button, 32×32px, `text-lexi-text-secondary hover:text-lexi-text`
  - **HISTORY** — `border-lexi border-lexi-border-muted shadow-lexi-sm`, Space Mono 10px 700 uppercase 0.12em tracking, secondary text. Hover: `shadow-lexi-md -translate-x-px -translate-y-px`
  - **LEAVE** — `border-lexi border-lexi-danger text-lexi-danger shadow-lexi-sm`, Space Mono 10px 700 uppercase 0.12em tracking. Hover: `shadow-lexi-md -translate-x-px -translate-y-px`

### Player Panel (×2 — opponent left/top, you right/bottom)

A compact card, 176px wide (w-44):

```
┌─────────────────────────────┐  ← 4px primary top border if active turn
│  ┌──────┐                   │     otherwise 2px standard border
│  │avatar│ ● Player Name     │
│  └──────┘                   │
│─────────────────────────────│
│                             │
│          137                │  ← 32px, 900 weight, tabular-nums
│                             │
│─────────────────────────────│
│  TIME          5:42  OT·1   │  ← micro label 10px / mono 16px
└─────────────────────────────┘
```

- `bg-lexi-panel`, `border-lexi border-lexi-panel-border`, `shadow-lexi-sm`
- Active turn: `border-t-4 border-t-lexi-panel-accent shadow-lexi-md`
- Inactive/disconnected: `opacity-50` (disconnected only)
- **Avatar:** 56×56px image, 1px border, with connection dot overlay (10px circle, positioned bottom-0.5 right-0.5, 2px border matching panel bg)
- **Connection dot:**
  - **Active turn + connected:** `bg-lexi-dot-active` + `box-shadow: 0 0 6px var(--color-dot-active)`
  - **Connected, not turn:** `bg-lexi-dot-waiting` + `animation: lexi-pulse-dot 2s ease-in-out infinite`
  - **Disconnected:** `bg-lexi-dot-offline`
- **Name:** Space Mono, 12px, 700, `-0.02em` tracking
- **Score:** Space Mono, 32px, 900 weight, `-0.02em` tracking, `font-variant-numeric: tabular-nums`
- **TIME label:** Space Mono, 10px, 900, uppercase, 0.12em tracking, muted
- **OT badge:** Shown when `overtime_count > 0`. Space Mono 10px 900, uppercase, `bg-lexi-warning` (1 OT) or `bg-lexi-danger` (2+ OT), dark text
- **Clock ticker:** Pings server timestamp, counts down in real-time while active turn, freezes otherwise. Space Mono, 16px, 700, `tabular-nums`. Turns `clock-urgent` when < 60s or in overtime

### Bag Indicator

Compact badge above the board:
- `bg-lexi-bg-sunken`, `border-lexi-light border-lexi-border`, inline-flex
- `bag.svg` icon (16×16) + remaining tile count in Space Mono 11px 700

### Board (15×15 Grid)

The visual anchor.
- **Container:** `border-lexi border-lexi-board-border`, `bg-lexi-board`, `shadow-lexi-lg`, padding 8px, no border-radius
- **Cells:** 36×36px each (`w-lexi-cell h-lexi-cell`), inside a 1px padding wrapper (`p-[1px]`)
  - `border-lexi-light` and `border-lexi-cell-border` (empty) or `border-lexi-placed-border` (occupied)
  - `rounded-lexi-xs`
  - Empty cells: flat bg per square type
  - Placed: `bg-lexi-placed` with letter in `text-lexi-placed-text` (EB Garamond 18px 600) and points in `text-lexi-placed-points` (Space Mono 8px 700, bottom-right)
- **Premium labels:** Space Mono, 10px, 700, 0.12em tracking, shown only when cell is empty
- **Ghost tiles:** Pending placements shown with `?` for blanks, muted styling
- **Blank picker:** Clicking a ghost blank tile opens an A–Z popover grid to assign its letter
- **Labels:** Row numbers (1–15) and column letters (A–O) on all four sides in Space Mono 12px 700

### Tile Tray (Rack)

A horizontal strip below the board:
- `bg-lexi-bg-sunken`, `border-lexi border-lexi-border`, `shadow-lexi-sm`, padding 6px
- 7 tile slots + 1 shuffle button, flex row with 6px gap
- Each tile: 44×44px (`w-lexi-tile h-lexi-tile`)
  - Default: `bg-lexi-tile`, `border-lexi border-lexi-tile-border`, `shadow-lexi-sm`
  - Hover: `shadow-lexi-tile-hover -translate-x-0.5 -translate-y-1`
  - Selected: `bg-lexi-tile-selected`, `shadow-lexi-tile-selected -translate-x-0.5 -translate-y-1.5`, `border-lexi-tile-selected-border`
  - Swap mode: `border-lexi-danger` tint
  - Transition: `all 200ms cubic-bezier(0.34, 1.20, 0.64, 1)` (overshoot spring)
- Letter: EB Garamond, 18px, 600; default `text-lexi-tile-text`; selected `text-lexi-tile-selected-text`
- Points: Space Mono, 10px, 700; default `text-lexi-tile-points`; selected `text-lexi-tile-selected-text`
- **Shuffle button:** 36×36px, `border-lexi border-lexi-border-muted`, `rounded-sm`, cross-arrows SVG

### Controls (below tile rack)

A horizontal row of 5 buttons, 8px gap, centered:
- **Submit** — `bg-lexi-primary text-lexi-text-on-accent`, `border-lexi border-lexi-border`, `shadow-lexi-md`, Space Mono 11px 700 uppercase 0.12em tracking, padding 8px 20px. Shown when tiles are placed or swap-selected. Hover: `shadow-lexi-lg -translate-x-px -translate-y-px`
- **Clear** — transparent bg, `border-lexi border-lexi-border-muted`, secondary text. Shown only when placements exist.
- **Swap / Cancel** — toggle button. Inactive: "SWAP" with standard ghost styling. Active: "CANCEL" with `border-lexi-danger` tint.
- **Pass** — transparent bg, `border-lexi border-lexi-border-muted`, secondary text
- **Forfeit** — `border-lexi border-lexi-danger text-lexi-danger`, `shadow-lexi-sm`, Space Mono 10px 700. Hover: `shadow-lexi-md -translate-x-px -translate-y-px`

---

## Screen 3: Game Over

When game phase is 'finished', the board remains visible but a centered overlay appears.

**Overlay:**
- Full-screen fixed, `bg-lexi-overlay` (semi-transparent backdrop)
- Card: `bg-lexi-overlay-card`, `border-lexi border-lexi-overlay-border`, `shadow-lexi-lg`, padding 32px, max-width 360px
- Top border: `border-t-4` — primary (won), amber (forfeit), or danger (timeout)

**Content:**
- Heading row: "YOU WON" / "YOU LOST" / "GAME OVER" — Space Mono, 11px, 700, uppercase, 0.12em tracking, secondary text
- Winner name — EB Garamond, 28px, 500, primary color
- Winner score — Space Mono, 36px, 700
- Final scores section:
  - Each player row: `bg-lexi-bg-sunken`, `border-lexi border-lexi-border-muted`. Flex row with avatar (32×32px) + name (EB Garamond 18px) + score (Space Mono 24px 700, tabular-nums)
  - Winner score: primary color | Loser score: danger color
- **Play Again** button — same style as primary Submit button

**End variants:**
- `normal`: Highest score wins. Heading alternates "YOU WON" / "YOU LOST"
- `forfeit`: Opponent forfeited. Heading "YOU WON" always for remaining player
- `timeout`: Opponent timed out. Heading "YOU WON" for remaining player

---

## Screen 4: Game Paused

When game phase is 'paused' (player disconnect):

**Overlay:**
- Full-screen fixed, `bg-lexi-overlay`
- Card: `bg-lexi-overlay-card`, `border-lexi border-lexi-overlay-border`, `shadow-lexi-lg`, `border-t-4 border-lexi-warning`
- "GAME PAUSED" — Space Mono, 11px, 700, uppercase, 0.12em tracking, warning color
- "Waiting for reconnection" — Space Mono, 12px, secondary text
- Players listed with CONNECTED / OFFLINE status labels (connected: `text-lexi-success`, offline: `text-lexi-text-muted`)
- **LEAVE GAME** — `border-lexi border-lexi-danger text-lexi-danger shadow-lexi-sm`, Space Mono 10px 700 uppercase

---

## Move History Sidebar

Slide-out panel toggled by the HISTORY button in the header.

**Structure:**
- Fixed left panel, 260px wide, `bg-lexi-bg-elevated`, `border-r-2 border-lexi-border`, `shadow-lexi-lg`
- Overlay scrim: `rgba(0,0,0,0.5)`, click to dismiss
- Slide transition: `transform 200ms ease`, from `translateX(-100%)`

**Header:**
- "MOVE HISTORY" — Space Mono, 11px, 700, uppercase, 0.12em tracking, secondary text
- Close button (✕)
- Legend: two swatches (10×10px) — mine (primary/yellow) / opponent (secondary/slate)

**Move list (reversed):**
- Each row: 6px 12px padding, bottom border
- Background: mine = primary-subtle, opponent = secondary-subtle
- Player name (uppercase, Space Mono 9px 700, 42px fixed width)
- Middle dot separator
- Word in EB Garamond 17px 500 (for place moves) | Action label in Space Mono 9px 700 (SWAP/PASS/FORFEIT/TIME OUT)
- Score delta (+24) in Space Mono 11px 700, tabular-nums, 34px fixed width

**Footer:**
- Space Mono 9px 700 uppercase, muted text
- Total move count + current scores

**Empty state:** "No moves yet" centered, 80px height, muted text.

---

## Toast System

Two-tier notification:

### BoardBanner (above the board)
- Fixed-height (36px) wrapper showing the most recent toast
- Dot color per type, click to dismiss
- Auto-height wrapper prevents layout shift

### ToastFooter (fixed overlay)
- Fixed-bottom 30px bar, full width
- `bg-lexi-notif`, `border-t-2 border-lexi-notif-border`
- Appears with `lexi-slide-up` animation (250ms, translateY 100% → 0)
- Single toast visible at a time, auto-cycles every 5s
- Colored dot: error = danger, success = success, warning = warning, info = primary
- Text: Space Mono 11px, `text-lexi-notif-text`
- Click to dismiss

---

## Theme Toggle

Light/dark mode controlled via `data-theme` attribute on `<html>`:
- `data-theme="light"` — cream paper surfaces, ink black borders, acid yellow accent
- `data-theme="dark"` — near-black surfaces, near-white borders, dusty olive accent

Toggle button appears in both LobbyView (top-right corner) and GameView header. Sun icon shown in dark mode (click goes light), moon icon in light mode (click goes dark). Persisted to `localStorage`. Default: system preference with light fallback.

---

## Avatar System

10 unique Multiavatar PNGs shipped in `src/assets/avatars/`.

**Where they appear:**
1. **Lobby:** 5-column grid picker, randomly assigned on mount. Selection highlighted with primary border + shadow offset.
2. **Player Panel:** 56×56px image with connection dot overlay. No image → plain dot only.
3. **Game Over:** 32×32px image next to each player's score row.

Avatar key (`avatar?: string`) sent with create/join API requests and stored in `PlayerSession`.

---

## Overtime System

When a player's clock reaches 0:
- `-10` point penalty applied
- `+60` seconds added to their clock
- `overtime_count` incremented per occurrence
- Toast notification: "nickname ran out of time — -10 pts, +60s overtime"
- PlayerPanel shows OT badge: `OT·1`, `OT·2`, etc.
  - 1 OT: `bg-lexi-warning` (amber)
  - 2+ OT: `bg-lexi-danger` (red)
- Clock text turns `clock-urgent` when in overtime or < 60s remaining

---

## Blank Tile Letter Picker

When a blank tile (letter ` `) is placed on the board as a ghost:
- Clicking the ghost opens a 7-column A–Z popover grid
- Selecting a letter locks it for that board position
- `blankLetterMap: Map<string, string>` tracks `"row,col" → letter` pairs

---

## Design Principles

1. **The board is king.** Everything else is chrome. The board should feel stamped into the page — hard shadow, thick border, no radius.
2. **Neo-brutalism is not a joke.** Hard shadows, thick borders, monospace UI. No blur, no gradient backgrounds on components (only flat fills), no rounded corners on containers.
3. **One action per tap.** Never ask the user to confirm. Submit sends immediately. Clear is instant.
4. **Silence is the interface.** Empty states are just empty space. No spinners unless loading. No toasts unless something happened.
5. **Dual-mode, equal citizens.** Light and dark are not afterthoughts — they're both first-class themes with their own palette mappings.
6. **Connection state is explicit.** Active turn = green + glow. Connected waiting = pulsing emerald. Disconnected = gray mute.
7. **Avatars are identity.** Every player gets a unique abstract avatar. The avatar is the primary visual identifier, not the nickname.
8. **History is a sidebar, not a ticker.** Moves are reviewed in a slide-out panel, not a bottom bar.
