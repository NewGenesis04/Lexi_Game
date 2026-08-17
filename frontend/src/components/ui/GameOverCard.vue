<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import type { PlayerOut } from '../../types/game'
import { AVATARS } from '../../constants/avatars'

const props = defineProps<{
  iAmWinner: boolean
  endReason: 'forfeit' | 'timeout' | 'normal'
  winner: PlayerOut | null
  draw: boolean
  players: PlayerOut[]
}>()

const emit = defineEmits<{ 'play-again': []; dismiss: [] }>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('dismiss')
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

const winnerName = computed(() => props.winner?.nickname ?? 'OPPONENT')

const heading = computed(() => {
  if (props.draw) return 'TIE'
  if (props.iAmWinner) return 'YOU WON'
  if (props.endReason === 'timeout' || props.endReason === 'forfeit') return `${winnerName.value} WON!`
  return 'YOU LOST'
})

const subLabel = computed(() => {
  if (props.draw) return 'GAME OVER'
  if (props.endReason === 'timeout') return props.iAmWinner ? 'TIME OUT' : 'TIMED OUT'
  if (props.endReason === 'forfeit') return 'FORFEITED'
  return 'GAME OVER'
})

const accentColor = computed(() => {
  if (props.draw) return 'var(--color-lexi-warning)'
  if (props.iAmWinner) return 'var(--color-lexi-primary)'
  if (props.endReason === 'timeout') return 'var(--color-lexi-warning)'
  return 'var(--color-lexi-danger)'
})

const headingClass = computed(() => {
  if (props.draw) return 'text-lexi-warning'
  if (props.iAmWinner) return 'text-lexi-primary'
  if (props.endReason === 'timeout') return 'text-lexi-warning'
  return 'text-lexi-danger'
})

function avatarSrc(p: PlayerOut): string | null {
  return p.avatar ? (AVATARS[p.avatar] ?? null) : null
}
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-lexi-overlay"
    @click.self="emit('dismiss')"
  >
    <div
      class="lexi-fade-in w-full max-w-sm bg-lexi-overlay-card border-lexi border-lexi-overlay-border border-t-4 shadow-lexi-lg p-8"
      :style="{ borderTopColor: accentColor }"
    >
      <!-- Outcome heading -->
      <div class="mb-6">
        <h2 :class="['font-lexi-ui text-lexi-2xl font-bold leading-none', headingClass]">
          {{ heading }}
        </h2>
        <p class="font-lexi-ui text-lexi-xs tracking-lexi-wide text-lexi-text-muted mt-2 uppercase">
          {{ subLabel }}
        </p>
      </div>

      <!-- Final scores -->
      <div class="flex flex-col gap-px mb-6">
        <p class="font-lexi-ui text-lexi-xs tracking-lexi-wide text-lexi-text-muted uppercase mb-2">
          Final Scores
        </p>
        <div
          v-for="p in players"
          :key="p.id"
          class="flex items-center justify-between px-4 py-3 bg-lexi-bg-sunken border-lexi-light border-lexi-border"
        >
          <div class="flex items-center gap-3">
            <img
              v-if="avatarSrc(p)"
              :src="avatarSrc(p)!"
              :alt="p.nickname"
              class="w-8 h-8 object-cover flex-shrink-0"
            />
            <span class="font-lexi-display text-lexi-lg text-lexi-text">{{ p.nickname }}</span>
          </div>
          <span
            :class="[
              'font-lexi-numeric text-lexi-xl font-bold lexi-numeric',
              draw || winner?.id === p.id ? headingClass : 'text-lexi-text-muted'
            ]"
          >
            {{ p.score }}
          </span>
        </div>
      </div>

      <!-- Action -->
      <button
        class="w-full py-3 bg-lexi-primary text-lexi-text-on-accent border-lexi border-lexi-border shadow-lexi-md font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
        @click="emit('play-again')"
      >
        PLAY AGAIN
      </button>
    </div>
  </div>
</template>
