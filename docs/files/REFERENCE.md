# Lexi — Design System Reference
## Neo-Brutalist | Vue 3 + Tailwind

---

## Setup

```css
/* main.css — before Tailwind directives */
@import './lexi.css';
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```html
<!-- index.html or App.vue — set theme on <html> -->
<html data-theme="light">   <!-- or "dark" -->
```

```js
// Toggle theme in Vue
const toggleTheme = () => {
  const html = document.documentElement
  html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark'
}
```

---

## The Neo-Brutalist Signature

Every interactive element follows the same physical metaphor:

| State   | Shadow            | Transform                        |
|---------|-------------------|----------------------------------|
| Default | `shadow-lexi-md`  | none                             |
| Hover   | `shadow-lexi-lg`  | `translate(-1px, -1px)`          |
| Active  | `shadow-lexi-pressed` | `translate(2px, 2px)`        |

```vue
<button class="
  bg-lexi-primary text-lexi-text-on-accent
  border-lexi border-lexi-border
  shadow-lexi-md font-lexi-ui text-lexi-sm tracking-lexi-wide
  transition-all duration-lexi-base
  hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px
  active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5
">
  SUBMIT
</button>
```

---

## Color Tokens (Tailwind classes)

### Surfaces
| Token                  | Tailwind class              | Usage                        |
|------------------------|-----------------------------|------------------------------|
| `--color-bg`           | `bg-lexi-bg`                | Page background              |
| `--color-bg-elevated`  | `bg-lexi-bg-elevated`       | Cards, panels, modals        |
| `--color-bg-sunken`    | `bg-lexi-bg-sunken`         | Rack, board inset, inputs    |

### Text
| Token                     | Tailwind class                | Usage                    |
|---------------------------|-------------------------------|--------------------------|
| `--color-text-primary`    | `text-lexi-text`              | Body copy, headings      |
| `--color-text-secondary`  | `text-lexi-text-secondary`    | Labels, captions         |
| `--color-text-muted`      | `text-lexi-text-muted`        | Hints, placeholders      |
| `--color-text-on-accent`  | `text-lexi-text-on-accent`    | Text on primary/yellow   |

### Brand & Accents
| Token               | Tailwind class         | Light mode         | Dark mode          |
|---------------------|------------------------|--------------------|--------------------|
| `--color-primary`   | `bg-lexi-primary`      | Acid Yellow        | Dusty Olive        |
| `--color-secondary` | `bg-lexi-secondary`    | Cobalt Blue        | Muted Slate        |
| `--color-danger`    | `bg-lexi-danger`       | Brick Red          | Muted Brick        |
| `--color-success`   | `bg-lexi-success`      | Forest Green       | Muted Forest       |
| `--color-warning`   | `bg-lexi-warning`      | Terracotta         | Muted Terracotta   |

### Borders
| Token                  | Tailwind class           | Light    | Dark     |
|------------------------|--------------------------|----------|----------|
| `--color-border`       | `border-lexi-border`     | #0F0F0F  | #E5E5E5  |
| `--color-border-subtle`| `border-lexi-border-subtle` | #333  | #AAA     |
| `--color-border-muted` | `border-lexi-border-muted`  | #AAA  | #333     |

---

## Board Square Tokens

Apply these directly in your BoardCell component:

```vue
<script setup>
const squareClasses = {
  DL:   'bg-lexi-sq-dl   border-lexi-sq-dl-border   text-lexi-sq-dl-label',
  TL:   'bg-lexi-sq-tl   border-lexi-sq-tl-border   text-lexi-sq-tl-label',
  DW:   'bg-lexi-sq-dw   border-lexi-sq-dw-border   text-lexi-sq-dw-label',
  TW:   'bg-lexi-sq-tw   border-lexi-sq-tw-border   text-lexi-sq-tw-label',
  STAR: 'bg-lexi-sq-star border-lexi-sq-star-border text-lexi-sq-star-label',
  NONE: 'bg-lexi-cell    border-lexi-cell-border',
}
</script>

<template>
  <div
    :class="[
      squareClasses[cell.type],
      'w-lexi-cell h-lexi-cell',
      'border-lexi-light',
      'rounded-lexi-xs',
      'flex items-center justify-center',
    ]"
  >
    <!-- label when empty -->
    <span
      v-if="!cell.tile && cell.type !== 'NONE'"
      class="font-lexi-ui text-lexi-xs tracking-lexi-wide font-bold"
    >
      {{ cell.label }}
    </span>
  </div>
</template>
```

---

## Typography

```html
<!-- Page / section title -->
<h1 class="font-lexi-display text-lexi-2xl text-lexi-text">LEXI</h1>

<!-- Board tile letter -->
<span class="font-lexi-display text-lexi-lg font-semibold">A</span>

<!-- UI label / button -->
<span class="font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase">Submit Word</span>

<!-- Score / clock -->
<span class="font-lexi-numeric text-lexi-xl tracking-lexi-tight lexi-numeric">137</span>
```

---

## Component Patterns

### Button — Primary
```vue
<button class="
  px-5 py-2
  bg-lexi-primary text-lexi-text-on-accent
  border-lexi border-lexi-border
  shadow-lexi-md
  font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold
  transition-all duration-lexi-base ease-lexi-spring
  hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px
  active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5
  disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0
">
  slot
</button>
```

### Button — Ghost / Outline
```vue
<button class="
  px-5 py-2
  bg-transparent text-lexi-text
  border-lexi border-lexi-border
  shadow-lexi-sm
  font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold
  transition-all duration-lexi-base
  hover:bg-lexi-bg-elevated hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px
  active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5
">
  slot
</button>
```

### Button — Danger (Forfeit)
```vue
<button class="
  px-5 py-2
  bg-lexi-danger text-lexi-text-on-dark
  border-lexi border-lexi-border
  shadow-lexi-sm
  font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold
  transition-all duration-lexi-base
  hover:bg-lexi-danger-hover hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px
  active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5
">
  FORFEIT
</button>
```

### Input
```vue
<input class="
  w-full px-3 py-2
  bg-lexi-bg-sunken text-lexi-text
  border-lexi border-lexi-border
  shadow-lexi-sm
  font-lexi-ui text-lexi-base tracking-lexi-ui
  placeholder:text-lexi-text-muted
  focus:outline-none focus:shadow-lexi-md focus:-translate-x-px focus:-translate-y-px
  transition-all duration-lexi-fast
" />
```

### Card / Panel
```vue
<div class="
  bg-lexi-bg-elevated
  border-lexi border-lexi-border
  shadow-lexi-md
  p-6
">
  slot
</div>
```

### Rack Tile
```vue
<div
  :class="[
    isSelected
      ? 'bg-lexi-tile-selected text-lexi-tile-selected-text border-lexi-border shadow-lexi-tile-selected -translate-x-0.5 -translate-y-1.5'
      : 'bg-lexi-tile text-lexi-tile-text border-lexi-tile-border shadow-lexi-tile',
    'w-lexi-tile h-lexi-tile',
    'border-lexi',
    'rounded-lexi-xs',
    'flex flex-col items-center justify-center cursor-pointer select-none',
    'transition-all ease-lexi-spring duration-lexi-spring',
    'hover:shadow-lexi-tile-hover hover:-translate-x-0.5 hover:-translate-y-1',
  ]"
>
  <span class="font-lexi-display text-lexi-lg font-semibold">{{ tile.letter }}</span>
  <span class="font-lexi-ui text-lexi-xs font-bold" :class="isSelected ? 'text-lexi-tile-selected-text' : 'text-lexi-tile-points'">
    {{ tile.points }}
  </span>
</div>
```

### Player Panel
```vue
<div
  :class="[
    'bg-lexi-panel border-lexi shadow-lexi-md',
    'w-lexi-panel',
    isActive
      ? 'border-t-[3px] border-t-lexi-panel-accent border-lexi-panel-border'
      : 'border-lexi-panel-border',
    isOffline && 'opacity-50',
  ]"
>
  <!-- name row -->
  <div class="flex items-center gap-2 px-4 py-3 border-b border-lexi-border-muted">
    <span
      :class="[
        'w-2 h-2 rounded-full',
        isActive  ? 'bg-lexi-dot-active' : '',
        isWaiting ? 'bg-lexi-dot-waiting animate-lexi-pulse-dot' : '',
        isOffline ? 'bg-lexi-dot-offline' : '',
      ]"
    />
    <span class="font-lexi-ui text-lexi-sm tracking-lexi-ui font-bold text-lexi-text truncate">
      {{ player.name }}
    </span>
  </div>
  <!-- score -->
  <div class="px-4 py-4 border-b border-lexi-border-muted flex items-center justify-center">
    <span class="font-lexi-numeric text-lexi-3xl font-black tracking-lexi-tight text-lexi-score lexi-numeric">
      {{ player.score }}
    </span>
  </div>
  <!-- clock -->
  <div class="px-4 py-3 flex items-center justify-between">
    <span class="font-lexi-ui text-lexi-xs tracking-lexi-wide text-lexi-text-muted uppercase font-bold">Time</span>
    <span
      class="font-lexi-numeric text-lexi-md font-bold lexi-numeric"
      :class="isUrgent ? 'text-lexi-clock-urgent' : 'text-lexi-text-secondary'"
    >
      {{ formattedTime }}
    </span>
  </div>
</div>
```

---

## Theme Toggle (Vue composable)

```js
// composables/useTheme.js
import { ref, watchEffect } from 'vue'

const theme = ref(
  localStorage.getItem('lexi-theme') ??
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
)

watchEffect(() => {
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('lexi-theme', theme.value)
})

export function useTheme() {
  const toggle = () => { theme.value = theme.value === 'dark' ? 'light' : 'dark' }
  return { theme, toggle }
}
```

---

## Palette Quick Reference

| Name         | Light mode role     | Dark mode role        |
|--------------|---------------------|-----------------------|
| Acid Yellow  | Primary / brand     | —                     |
| Dusty Olive  | —                   | Primary / brand       |
| Cobalt Blue  | Secondary, DL sq    | Muted Slate (DL sq)   |
| Brick Red    | Danger, TW sq       | Muted Brick (TW sq)   |
| Forest Green | Success, DW sq      | Muted Forest (DW sq)  |
| Terracotta   | Warning, TL sq      | Muted Terra (TL sq)   |
| Cream paper  | Page / surfaces     | —                     |
| Near-black   | Borders (light)     | Surfaces (dark)       |
| Near-white   | —                   | Borders (dark)        |
