<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import type { PlayerOut } from '../../types/game'
import { AVATARS } from '../../constants/avatars'

const props = defineProps<{
  player: PlayerOut | null
  position: 'top' | 'bottom'
  isActiveTurn: boolean
  connected: boolean
  avatarKey?: string
}>()

const avatarSrc = computed(() => {
  const key = props.avatarKey ?? props.player?.avatar
  return key ? (AVATARS[key] ?? null) : null
})

const displaySeconds = ref(0)
let serverBase = 0
let baseTimestamp = 0
let ticker: ReturnType<typeof setInterval> | null = null

function stopTicker() {
  if (ticker !== null) { clearInterval(ticker); ticker = null }
}

function startTicker() {
  stopTicker()
  ticker = setInterval(() => {
    displaySeconds.value = Math.max(0, Math.ceil(serverBase - (Date.now() - baseTimestamp) / 1000))
  }, 1000)
}

watch(() => props.player?.time_remaining_secs, (val) => {
  if (val !== undefined) {
    serverBase = val
    baseTimestamp = Date.now()
    displaySeconds.value = Math.ceil(val)
  }
}, { immediate: true })

watch(() => props.isActiveTurn, (active) => {
  if (active && props.player) {
    baseTimestamp = Date.now()
    displaySeconds.value = Math.ceil(serverBase)
    startTicker()
  } else {
    stopTicker()
  }
}, { immediate: true })

onUnmounted(() => stopTicker())

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

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

const isOvertime = computed(() => (props.player?.overtime_count ?? 0) > 0)
const isClockUrgent = computed(() => isOvertime.value || displaySeconds.value < 60)

const cardStyle = computed(() => {
  if (props.isActiveTurn && props.connected) {
    return { borderTopColor: 'var(--color-panel-active-accent)' }
  }
  return {}
})
</script>

<template>
  <div
    class="w-44 flex-shrink-0 transition-opacity duration-300"
    :class="connected !== false ? 'opacity-100' : 'opacity-50'"
  >
    <div
      class="panel-card p-3.5 transition-all duration-lexi-base"
      :class="isActiveTurn && connected ? 'border-t-4 shadow-lexi-md' : 'shadow-lexi-sm'"
      :style="cardStyle"
    >
      <!-- Avatar -->
      <div v-if="avatarSrc" class="relative mb-3 flex justify-center">
        <div class="relative" style="width: 56px; height: 56px;">
          <img
            :src="avatarSrc"
            alt="avatar"
            class="w-14 h-14 object-cover"
          />
          <span
            class="absolute bottom-0.5 right-0.5 w-2.5 h-2.5 rounded-full"
            style="border: 2px solid var(--color-panel-bg);"
            :style="dotStyle"
          />
        </div>
      </div>

      <!-- Name row -->
      <div class="flex items-center gap-2 min-w-0">
        <span
          v-if="!avatarSrc"
          class="w-1.5 h-1.5 rounded-full flex-shrink-0"
          :style="dotStyle"
        />
        <span class="font-lexi-ui text-lexi-sm font-bold tracking-lexi-tight leading-tight truncate"
          :class="player ? 'text-lexi-text' : 'text-lexi-text-muted'"
        >
          {{ player ? player.nickname : 'Waiting…' }}
        </span>
      </div>

      <div class="border-t border-lexi-border-muted my-3" />

      <template v-if="player">
        <!-- Score -->
        <div class="text-center mb-2.5">
          <span class="font-lexi-numeric text-lexi-2xl font-black text-lexi-text lexi-numeric">
            {{ player.score }}
          </span>
        </div>

        <div class="border-t border-lexi-border-muted mb-2.5" />

        <!-- Clock row -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1">
            <span class="font-lexi-ui text-lexi-xs font-black tracking-lexi-wide text-lexi-text-muted uppercase">TIME</span>
            <span
              v-if="isOvertime"
              class="font-lexi-ui text-lexi-xs font-black px-1 leading-normal uppercase"
              :class="player.overtime_count >= 2 ? 'bg-lexi-danger' : 'bg-lexi-warning'"
              style="color: var(--color-text-on-dark);"
            >OT·{{ player.overtime_count }}</span>
          </div>
          <span
            class="font-lexi-numeric text-lexi-base font-bold lexi-numeric"
            :style="{ color: isClockUrgent ? 'var(--color-panel-clock-urgent)' : 'var(--color-text-primary)' }"
          >
            {{ formatTime(displaySeconds) }}
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.panel-card {
  background: var(--color-panel-bg);
  border: 2px solid var(--color-panel-border);
}
</style>
