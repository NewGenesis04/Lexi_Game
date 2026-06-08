<script setup lang="ts">
import type { PlayerOut } from '../../types/game'

defineProps<{
  players: PlayerOut[]
}>()

const emit = defineEmits<{ leave: [] }>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-lexi-overlay">
    <div
      class="lexi-fade-in w-full max-w-sm bg-lexi-overlay-card border-lexi border-lexi-overlay-border border-t-4 shadow-lexi-lg p-8"
      style="border-top-color: var(--color-lexi-warning);"
    >
      <!-- Heading -->
      <div class="mb-6">
        <h2 class="font-lexi-ui text-lexi-2xl font-bold leading-none text-lexi-warning">
          GAME PAUSED
        </h2>
        <p class="font-lexi-ui text-lexi-xs tracking-lexi-wide text-lexi-text-muted mt-2 uppercase">
          Waiting for reconnection
        </p>
      </div>

      <!-- Player connection status -->
      <div class="flex flex-col gap-px mb-6">
        <div
          v-for="p in players"
          :key="p.id"
          :class="[
            'flex items-center justify-between px-4 py-3 bg-lexi-bg-sunken border-lexi-light border-lexi-border transition-opacity duration-lexi-base',
            !p.connected && 'opacity-50'
          ]"
        >
          <span class="font-lexi-display text-lexi-lg text-lexi-text">{{ p.nickname }}</span>
          <span
            :class="[
              'font-lexi-ui text-lexi-xs tracking-lexi-wide font-bold uppercase',
              p.connected ? 'text-lexi-success' : 'text-lexi-text-muted'
            ]"
          >
            {{ p.connected ? 'CONNECTED' : 'OFFLINE' }}
          </span>
        </div>
      </div>

      <!-- Action -->
      <button
        class="w-full py-3 bg-lexi-danger text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
        @click="emit('leave')"
      >
        LEAVE GAME
      </button>
    </div>
  </div>
</template>
