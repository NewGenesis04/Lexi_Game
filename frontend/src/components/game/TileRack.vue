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

function tileStateClass(i: number): string {
  if (props.placedIndices.has(i) && props.selectedIndex !== i) return 'tile--placed'
  if (props.swapIndices.has(i)) return 'tile--swap'
  if (props.selectedIndex === i) return 'tile--selected'
  return 'tile--normal'
}
</script>

<template>
  <div class="rack-container inline-flex items-center gap-1.5 px-1.5 py-1.5">
    <template v-if="tiles.length">
      <button
        v-for="i in shuffleOrder"
        :key="i"
        :data-rack-index="i"
        :class="['tile', 'relative', 'flex', 'flex-col', 'items-center', 'justify-center', 'w-lexi-tile', 'h-lexi-tile', tileStateClass(i)]"
        @click="emit('selectTile', i)"
      >
        <span class="tile-letter">
          {{ tiles[i].letter === ' ' ? '?' : tiles[i].letter }}
        </span>
        <span class="tile-pts">{{ tiles[i].points }}</span>
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
      class="flex items-center justify-center w-lexi-panel h-lexi-tile font-lexi-ui text-lexi-xs text-lexi-text-muted"
    >
      No tiles
    </div>
  </div>
</template>

<style scoped>
.rack-container {
  background: var(--color-tile-rack-bg);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.tile {
  background: var(--color-tile-bg);
  border: 2px solid var(--color-tile-border);
  color: var(--color-tile-text);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 200ms cubic-bezier(0.34, 1.20, 0.64, 1);
}
.tile--normal:hover {
  box-shadow: var(--tile-hover-shadow);
  transform: var(--tile-hover-translate);
}
.tile--selected {
  background: var(--color-tile-selected-bg);
  border-color: var(--color-tile-selected-border);
  color: var(--color-tile-selected-text);
  box-shadow: var(--tile-selected-shadow);
  transform: var(--tile-selected-translate);
}
.tile--swap {
  background: var(--color-secondary-subtle);
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  box-shadow: var(--shadow-sm);
  transform: translate(-1px, -3px);
}
.tile--placed {
  opacity: 0.35;
  transform: scale(0.9);
  cursor: default;
}

.tile-letter {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  line-height: 1;
}
.tile-pts {
  position: absolute;
  bottom: 3px;
  right: 4px;
  font-family: var(--font-ui);
  font-size: 8px;
  font-weight: 700;
  line-height: 1;
  opacity: 0.7;
}

.shuffle-btn {
  width: 36px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border-muted);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 150ms;
  flex-shrink: 0;
}
.shuffle-btn:hover {
  border-color: var(--color-border);
  color: var(--color-text-primary);
}
</style>
