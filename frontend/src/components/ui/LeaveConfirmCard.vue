<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

defineProps<{
  opponentNickname: string
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('cancel')
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-lexi-overlay"
    @click.self="emit('cancel')"
  >
    <div
      class="lexi-fade-in w-full max-w-sm bg-lexi-overlay-card border-lexi border-lexi-overlay-border border-t-4 shadow-lexi-lg p-8"
      style="border-top-color: var(--color-lexi-danger);"
    >
      <!-- Heading -->
      <div class="mb-6">
        <h2 class="font-lexi-ui text-lexi-2xl font-bold leading-none text-lexi-danger">
          LEAVE GAME?
        </h2>
        <p class="font-lexi-ui text-lexi-xs tracking-lexi-wide text-lexi-text-muted mt-2 uppercase">
          Forfeits the game — {{ opponentNickname }} wins
        </p>
      </div>

      <!-- Actions -->
      <div class="flex gap-3">
        <button
          class="flex-1 py-3 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
          @click="emit('cancel')"
        >
          CANCEL
        </button>
        <button
          class="flex-1 py-3 bg-lexi-danger text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
          @click="emit('confirm')"
        >
          FORFEIT &amp; LEAVE
        </button>
      </div>
    </div>
  </div>
</template>
