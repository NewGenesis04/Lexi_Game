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

function tileClasses(i: number) {
  const base = 'flex h-10 w-10 items-center justify-center rounded text-lg font-bold shadow cursor-pointer transition-all'
  if (props.swapIndices.has(i)) return `${base} bg-yellow-400 text-neutral-900 ring-2 ring-yellow-300 scale-110`
  if (props.selectedIndex === i) return `${base} bg-amber-100 text-neutral-900 ring-2 ring-blue-400`
  if (props.swapMode) return `${base} bg-amber-100 text-neutral-900 opacity-70 hover:opacity-100`
  return `${base} bg-amber-100 text-neutral-900 hover:ring-2 hover:ring-blue-300`
}
</script>

<template>
  <div class="flex gap-1">
    <button
      v-for="(tile, i) in tiles"
      :key="i"
      :class="tileClasses(i)"
      @click="emit('selectTile', i)"
    >
      {{ tile.letter === ' ' ? '?' : tile.letter }}
    </button>
    <div
      v-if="!tiles.length"
      class="flex h-10 w-64 items-center justify-center rounded bg-neutral-700 text-sm text-neutral-400"
    >
      No tiles
    </div>
  </div>
</template>
