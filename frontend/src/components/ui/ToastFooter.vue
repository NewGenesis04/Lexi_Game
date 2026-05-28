<script setup lang="ts">
import { useGameStore } from '../../stores/game'

const store = useGameStore()
</script>

<template>
  <div
    v-if="store.toasts.length"
    class="fixed bottom-0 left-0 right-0 z-50 flex flex-col items-center gap-2 p-4"
  >
    <div
      v-for="toast in store.toasts"
      :key="toast.id"
      :class="[
        'w-full max-w-md rounded px-4 py-2 text-center text-sm shadow-lg',
        toast.type === 'error'
          ? 'bg-red-700 text-white'
          : toast.type === 'success'
            ? 'bg-green-700 text-white'
            : 'bg-neutral-700 text-white',
      ]"
    >
      {{ toast.text }}
    </div>
  </div>
</template>
