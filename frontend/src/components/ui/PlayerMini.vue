<script setup lang="ts">
import { computed, toRef } from 'vue'
import type { PlayerOut } from '../../types/game'
import { AVATARS } from '../../constants/avatars'
import { useClocks, formatTime } from '../../composables/useClocks'

const props = defineProps<{
  player: PlayerOut | null
  align: 'left' | 'right'
  isActiveTurn: boolean
  connected: boolean
  avatarKey?: string
}>()

const avatarSrc = computed(() => {
  const key = props.avatarKey ?? props.player?.avatar
  return key ? (AVATARS[key] ?? null) : null
})

const { displaySeconds, isOvertime, isClockUrgent } = useClocks(
  toRef(props, 'player'),
  toRef(props, 'isActiveTurn'),
)

const dotStyle = computed(() => {
  if (!props.player) return { background: 'var(--color-dot-offline)' }
  if (props.isActiveTurn && props.connected) {
    return { background: 'var(--color-dot-active)', boxShadow: '0 0 6px var(--color-dot-active)' }
  }
  if (props.connected) {
    return { background: 'var(--color-dot-waiting)', animation: 'lexi-pulse-dot 2s ease-in-out infinite' }
  }
  return { background: 'var(--color-dot-offline)' }
})

// Active-turn ring around the avatar — a second, unambiguous cue distinct
// from the connection dot (which conflates online/waiting/offline).
const avatarRingStyle = computed(() => {
  if (props.player && props.isActiveTurn && props.connected) {
    return { boxShadow: '0 0 0 2px var(--color-panel-active-accent)' }
  }
  return {}
})
</script>

<template>
  <div
    class="flex min-w-0 flex-1 items-center gap-1.5"
    :class="align === 'right' ? 'flex-row-reverse' : ''"
  >
    <div
      class="relative flex-shrink-0 transition-shadow duration-lexi-fast"
      style="width: 30px; height: 30px;"
      :style="avatarRingStyle"
    >
      <img
        v-if="avatarSrc"
        :src="avatarSrc"
        alt="avatar"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full bg-lexi-bg-sunken border-lexi-light border-lexi-border" />
      <span
        class="absolute bottom-0 right-0 w-2 h-2 rounded-full"
        style="border: 1.5px solid var(--color-panel-bg);"
        :style="dotStyle"
      />
    </div>

    <div class="flex min-w-0 flex-col" :class="align === 'right' ? 'items-end' : 'items-start'">
      <span
        class="font-lexi-ui text-lexi-xs font-bold tracking-lexi-tight truncate max-w-[88px]"
        :class="player ? 'text-lexi-text' : 'text-lexi-text-muted'"
      >
        {{ player ? player.nickname : 'Waiting…' }}
      </span>
      <div v-if="player" class="flex items-center gap-1.5" :class="align === 'right' ? 'flex-row-reverse' : ''">
        <span class="font-lexi-numeric text-lexi-base font-black lexi-numeric text-lexi-text">
          {{ player.score }}
        </span>
        <span
          class="font-lexi-numeric text-lexi-xs font-bold lexi-numeric"
          :style="{ color: isClockUrgent ? 'var(--color-panel-clock-urgent)' : 'var(--color-text-secondary)' }"
        >
          {{ formatTime(displaySeconds) }}
        </span>
        <span
          v-if="isOvertime"
          class="font-lexi-ui text-[9px] font-black px-1 leading-normal uppercase"
          :class="player.overtime_count >= 2 ? 'bg-lexi-danger' : 'bg-lexi-warning'"
          style="color: var(--color-text-on-dark);"
        >OT</span>
      </div>
    </div>
  </div>
</template>
