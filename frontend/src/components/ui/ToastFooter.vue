<script setup lang="ts">
import { useGameStore } from '../../stores/game'

const store = useGameStore()
</script>

<template>
  <div
    v-if="store.toasts.length"
    class="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-center"
    style="height: 30px; background: var(--color-surface-container-low); border-top: 1px solid var(--color-outline-variant);"
  >
    <span
      v-for="toast in store.toasts.slice(0, 1)"
      :key="toast.id"
      class="flex items-center gap-2 px-4"
    >
      <span
        :style="{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          display: 'inline-block',
          background: toast.type === 'error' ? 'var(--color-tertiary)' : toast.type === 'success' ? '#4caf50' : toast.type === 'warning' ? '#f59e0b' : 'var(--color-outline)',
        }"
      />
      <span style="font-family: var(--font-sans); font-size: 12px; color: var(--color-on-surface-variant); line-height: 1;">
        <strong style="color: var(--color-on-surface); font-weight: 600;">{{ toast.text }}</strong>
      </span>
    </span>
  </div>
</template>
