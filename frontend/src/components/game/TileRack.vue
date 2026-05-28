<script setup lang="ts">
import type { Tile } from '../../types/game'

const props = defineProps<{
  tiles: Tile[]
  selectedIndex: number | null
  placedIndices: Set<number>
  swapMode: boolean
  swapIndices: Set<number>
}>()

const emit = defineEmits<{
  selectTile: [index: number]
}>()

function tileStyle(i: number) {
  const isSelected = props.selectedIndex === i
  const isPlaced = props.placedIndices.has(i)
  const isSwap = props.swapIndices.has(i)
  const swapActive = props.swapMode

  let bg: string
  let border: string
  let boxShadow: string
  let transform: string
  let color: string
  let opacity: string

  if (isSwap) {
    bg = 'linear-gradient(180deg, #2a2a2a, #202020)'
    border = '1px solid var(--color-primary)'
    boxShadow = 'var(--shadow-tile-selected)'
    transform = 'translateY(-3px) scale(1.04)'
    color = 'var(--color-on-surface-variant)'
    opacity = '1'
  } else if (isSelected) {
    bg = 'linear-gradient(180deg, var(--color-primary), var(--color-primary-fixed-dim))'
    border = '1px solid var(--color-primary)'
    boxShadow = 'var(--shadow-tile-selected)'
    transform = 'translateY(-6px)'
    color = 'var(--color-on-primary)'
    opacity = '1'
  } else if (swapActive) {
    bg = 'linear-gradient(180deg, var(--color-surface-container-high), var(--color-surface-container))'
    border = '1px solid var(--color-outline-variant)'
    boxShadow = 'var(--shadow-tile-default)'
    transform = 'none'
    color = 'var(--color-on-surface-variant)'
    opacity = '1'
  } else {
    bg = 'linear-gradient(180deg, var(--color-surface-container-high), var(--color-surface-container))'
    border = '1px solid var(--color-outline-variant)'
    boxShadow = 'var(--shadow-tile-default)'
    transform = 'none'
    color = 'var(--color-on-surface-variant)'
    opacity = '1'
  }

  if (isPlaced && !isSelected) {
    opacity = '0.35'
    transform = 'scale(0.9)'
  }

  return {
    background: bg,
    border,
    boxShadow,
    transform,
    color,
    opacity,
    transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
    cursor: 'pointer',
    borderRadius: '0.25rem',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    width: '44px',
    height: '44px',
  }
}

function tileHover(i: number, entering: boolean) {
  if (props.selectedIndex === i || props.swapIndices.has(i) || props.placedIndices.has(i)) return
  const el = document.querySelector<HTMLElement>(`[data-rack-index="${i}"]`)
  if (!el) return
  if (entering) {
    el.style.background = 'linear-gradient(180deg, var(--color-surface-container-highest), var(--color-surface-container-high))'
    el.style.boxShadow = 'var(--shadow-tile-hover)'
    el.style.transform = 'translateY(-3px) scale(1.06)'
  } else {
    el.style.background = ''
    el.style.boxShadow = ''
    el.style.transform = ''
  }
}
</script>

<template>
  <div
    class="rack-container"
    style="display: inline-flex; padding: 6px; gap: 6px;"
  >
    <button
      v-for="(tile, i) in tiles"
      :key="i"
      :data-rack-index="i"
      :style="tileStyle(i)"
      @click="emit('selectTile', i)"
      @mouseenter="tileHover(i, true)"
      @mouseleave="tileHover(i, false)"
    >
      <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '20px', fontWeight: 600, lineHeight: '1', color: tileStyle(i).color, textShadow: '0 1px 2px rgba(0,0,0,0.5)' }">
        {{ tile.letter === ' ' ? '?' : tile.letter }}
      </span>
    </button>

    <div
      v-if="!tiles.length"
      class="flex items-center justify-center"
      style="width: 176px; height: 44px; font-family: var(--font-sans); font-size: 12px; color: var(--color-on-surface-variant);"
    >
      No tiles
    </div>
  </div>
</template>

<style scoped>
.rack-container {
  background: linear-gradient(180deg, var(--color-surface-container-low), var(--color-surface-container));
  border-radius: var(--radius-panel);
  border: 1px solid var(--color-outline-variant);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3);
}
</style>
