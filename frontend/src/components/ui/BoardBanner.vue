<script setup lang="ts">
import { computed } from 'vue'
import { useGameStore } from '../../stores/game'

const store = useGameStore()
const toast = computed(() => store.toasts[0] ?? null)

const dotClass: Record<string, string> = {
  error:   'bg-lexi-danger',
  success: 'bg-lexi-success',
  warning: 'bg-lexi-warning',
  info:    'bg-lexi-border-subtle',
}
</script>

<template>
  <!-- Fixed-height wrapper prevents layout shift when banner appears/disappears -->
  <div class="flex justify-center items-end" style="height: 36px;">
    <Transition name="banner">
      <div
        v-if="toast"
        class="flex items-center gap-2 px-4 bg-lexi-notif text-lexi-notif-text border-lexi-light border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-ui cursor-default select-none"
        style="height: 28px; white-space: nowrap;"
        @click="store.clearToasts()"
      >
        <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', dotClass[toast.type] ?? 'bg-lexi-border-subtle']" />
        <span>{{ toast.text }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.banner-enter-active {
  animation: lexi-slide-up 250ms ease forwards;
}
.banner-leave-active {
  transition: opacity 250ms ease;
}
.banner-leave-to {
  opacity: 0;
}
</style>
