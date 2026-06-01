<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TileOut } from '../../types/game'

const props = defineProps<{
  tiles: TileOut[]
  selectedIndex: number | null
  placedIndices: Set<number>
  swapMode: boolean
  swapIndices: Set<number>
}>()

const emit = defineEmits<{
  selectTile: [index: number]
}>()

const shuffleOrder = ref<number[]>([])

// Keyed on tile letters so the order only resets when your actual rack changes,
// not when an unrelated SSE update delivers a new game object reference.
const tileSignature = computed(() => props.tiles.map(t => t.letter).join(','))

watch(tileSignature, () => {
  shuffleOrder.value = props.tiles.map((_, i) => i)
}, { immediate: true })

function shuffle() {
  const arr = [...shuffleOrder.value]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  shuffleOrder.value = arr
}

function tileStyle(originalIndex: number) {
  const isSelected = props.selectedIndex === originalIndex
  const isPlaced = props.placedIndices.has(originalIndex)
  const isSwap = props.swapIndices.has(originalIndex)
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
    position: 'relative' as const,
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

function tileHover(originalIndex: number, entering: boolean) {
  if (props.selectedIndex === originalIndex || props.swapIndices.has(originalIndex) || props.placedIndices.has(originalIndex)) return
  const el = document.querySelector<HTMLElement>(`[data-rack-index="${originalIndex}"]`)
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
  <div class="rack-container" style="display: inline-flex; padding: 6px; gap: 6px;">
    <template v-if="tiles.length">
      <button
        v-for="originalIndex in shuffleOrder"
        :key="originalIndex"
        :data-rack-index="originalIndex"
        :style="tileStyle(originalIndex)"
        @click="emit('selectTile', originalIndex)"
        @mouseenter="tileHover(originalIndex, true)"
        @mouseleave="tileHover(originalIndex, false)"
      >
        <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '20px', fontWeight: 600, lineHeight: '1', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }">
          {{ tiles[originalIndex].letter === ' ' ? '?' : tiles[originalIndex].letter }}
        </span>
        <span class="tile-pts">{{ tiles[originalIndex].points }}</span>
      </button>

      <button class="shuffle-btn" title="Shuffle tiles" @click="shuffle">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="16 3 21 3 21 8"/>
          <line x1="4" y1="20" x2="21" y2="3"/>
          <polyline points="21 16 21 21 16 21"/>
          <line x1="15" y1="15" x2="21" y2="21"/>
          <line x1="4" y1="4" x2="9" y2="9"/>
        </svg>
      </button>
    </template>

    <div
      v-else
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

.tile-pts {
  position: absolute;
  bottom: 3px;
  right: 4px;
  font-family: var(--font-sans);
  font-size: 8px;
  font-weight: 700;
  line-height: 1;
  opacity: 0.75;
}

.shuffle-btn {
  width: 36px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-outline-variant);
  border-radius: 0.25rem;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.shuffle-btn:hover {
  background: var(--color-surface-container-high);
  border-color: var(--color-outline);
  color: var(--color-on-surface);
}
</style>
