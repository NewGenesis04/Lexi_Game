<script setup lang="ts">
import { computed } from 'vue'
import type { PlayerOut } from '../../types/game'

const props = defineProps<{
  player: PlayerOut | null
  position: 'top' | 'bottom'
  isActiveTurn: boolean
  connected: boolean
}>()

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

const dotState = computed(() => {
  if (!props.player) return { background: '#6b7280', boxShadow: 'none', animation: 'none' }
  if (props.isActiveTurn && props.connected) {
    return {
      background: '#10b981',
      boxShadow: '0 0 6px rgba(16,185,129,0.5)',
      animation: 'none',
    }
  }
  if (props.connected) {
    return {
      background: '#34d399',
      boxShadow: '0 0 6px rgba(16,185,129,0.5)',
      animation: 'pulse 2s ease-in-out infinite',
    }
  }
  return { background: '#6b7280', boxShadow: 'none', animation: 'none' }
})
</script>

<template>
  <div
    class="w-44 flex-shrink-0"
    :style="{ opacity: connected !== false ? 1 : 0.5 }"
  >
    <div
      :style="{
        background: 'rgba(38,38,38,0.4)',
        borderRadius: 'var(--radius-panel)',
        border: '1px solid rgba(96,96,96,0.3)',
        borderTop: isActiveTurn && connected ? '2px solid #10b981' : '1px solid rgba(96,96,96,0.3)',
        padding: '14px',
      }"
    >
      <div class="flex items-center gap-2">
        <span
          :style="{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            display: 'inline-block',
            background: dotState.background,
            boxShadow: dotState.boxShadow,
            animation: dotState.animation,
          }"
        />
        <span
          v-if="player"
          :style="{ fontFamily: 'var(--font-panel)', fontSize: '14px', fontWeight: 700, color: '#e5e5e5', letterSpacing: '-0.02em', lineHeight: '1.2' }"
        >
          {{ player.nickname }}
        </span>
        <span
          v-else
          :style="{ fontFamily: 'var(--font-panel)', fontSize: '14px', fontWeight: 700, color: '#6b7280', letterSpacing: '-0.02em', lineHeight: '1.2' }"
        >
          Waiting…
        </span>
      </div>

      <div :style="{ borderTop: '1px solid rgba(96,96,96,0.2)', margin: '12px 0 10px' }" />

      <template v-if="player">
        <div class="text-center" :style="{ marginBottom: '10px' }">
          <div :style="{ fontFamily: 'var(--font-panel)', fontSize: '36px', fontWeight: 900, color: '#fff', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums', lineHeight: '1' }">
            {{ player.score }}
          </div>
        </div>

        <div :style="{ borderTop: '1px solid rgba(96,96,96,0.2)', marginBottom: '10px' }" />

        <div class="flex items-center justify-between">
          <span :style="{ fontFamily: 'var(--font-panel)', fontSize: '9px', fontWeight: 900, letterSpacing: '0.15em', color: '#6b7280' }">TIME</span>
          <span :style="{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 700, letterSpacing: '-0.02em', color: player.time_remaining_secs < 60 ? 'var(--color-panel-clock-warning)' : 'var(--color-panel-clock)', fontVariantNumeric: 'tabular-nums' }">
            {{ formatTime(player.time_remaining_secs) }}
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<style>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
