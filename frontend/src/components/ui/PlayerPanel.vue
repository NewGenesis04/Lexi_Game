<script setup lang="ts">
import type { PlayerState } from '../../types/game'

defineProps<{
  player: PlayerState | null
  position: 'top' | 'bottom'
}>()
</script>

<template>
  <div class="w-48 rounded-lg bg-neutral-800 p-4 shadow">
    <div class="text-sm text-neutral-400">
      {{ position === 'top' ? 'Opponent' : 'You' }}
    </div>
    <div
      v-if="player"
      class="mt-1 space-y-1"
    >
      <div class="font-semibold">
        {{ player.nickname }}
      </div>
      <div class="text-lg font-bold text-blue-400">
        {{ player.score }}
      </div>
      <div class="text-xs text-neutral-400">
        {{ Math.floor(player.time_remaining / 60) }}:{{ String(player.time_remaining % 60).padStart(2, '0') }}
      </div>
      <div
        v-if="player.is_current_player"
        class="text-xs font-medium text-green-400"
      >
        ● Current turn
      </div>
    </div>
    <div
      v-else
      class="mt-1 text-sm text-neutral-500"
    >
      Waiting…
    </div>
  </div>
</template>
