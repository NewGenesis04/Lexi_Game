<script setup lang="ts">
import type { BoardTheme } from '../../types/game'

defineProps<{
  themes: BoardTheme[]
  current: string
  open: boolean
}>()

const emit = defineEmits<{
  select: [name: string]
  close: []
}>()
</script>

<template>
  <teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-40"
      @click="emit('close')"
    />
    <div
      v-if="open"
      class="absolute right-0 top-full z-50 mt-2 w-72 rounded-lg border border-neutral-600 bg-neutral-800 p-3 shadow-xl"
    >
      <h3 class="mb-3 text-center text-xs font-semibold uppercase tracking-wider text-neutral-400">
        Board Theme
      </h3>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="t in themes"
          :key="t.name"
          :class="[
            'flex flex-col items-center gap-1 rounded-lg p-2 transition hover:bg-neutral-700',
            current === t.name ? 'ring-2 ring-blue-500 bg-neutral-700' : '',
          ]"
          @click="emit('select', t.name)"
        >
          <div
            class="h-10 w-full rounded border"
            :class="[t.boardBg, t.border]"
            :style="{ borderWidth: '2px' }"
          />
          <span class="text-[10px] text-neutral-300">{{ t.name }}</span>
        </button>
      </div>
    </div>
  </teleport>
</template>
