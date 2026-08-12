import { ref, computed, watch, onUnmounted, type Ref } from 'vue'
import type { PlayerOut } from '../types/game'

export function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

/** Local countdown for one player's clock: re-anchors to the server value
 * whenever it changes, ticks locally between server pushes while it's their
 * turn. */
export function useClocks(player: Ref<PlayerOut | null>, isActiveTurn: Ref<boolean>) {
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

  watch(() => player.value?.time_remaining_secs, (val) => {
    if (val !== undefined) {
      serverBase = val
      baseTimestamp = Date.now()
      displaySeconds.value = Math.ceil(val)
    }
  }, { immediate: true })

  watch(isActiveTurn, (active) => {
    if (active && player.value) {
      baseTimestamp = Date.now()
      displaySeconds.value = Math.ceil(serverBase)
      startTicker()
    } else {
      stopTicker()
    }
  }, { immediate: true })

  onUnmounted(() => stopTicker())

  const isOvertime = computed(() => (player.value?.overtime_count ?? 0) > 0)
  const isClockUrgent = computed(() => isOvertime.value || displaySeconds.value < 60)

  return { displaySeconds, isOvertime, isClockUrgent }
}
