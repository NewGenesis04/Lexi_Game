<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { usePendingMove } from '../composables/usePendingMove'
import { useTheme } from '../composables/useTheme'
import GameBoard from '../components/game/GameBoard.vue'
import TileRack from '../components/game/TileRack.vue'
import PlayerPanel from '../components/ui/PlayerPanel.vue'
import MoveControls from '../components/ui/MoveControls.vue'
import ThemePicker from '../components/settings/ThemePicker.vue'

const route = useRoute()
const router = useRouter()
const store = useGameStore()
const { themeName, setTheme, availableThemes } = useTheme()
const {
  selectedRackIndex,
  ghosts,
  swapMode,
  swapIndices,
  blankLetterMap,
  hasPendingPlacements,
  hasSwapSelection,
  buildMovePayload,
  selectRackTile,
  tryPlaceTile,
  tryRemoveGhost,
  ghostAt,
  clearAll,
  toggleSwapMode,
  setBlankLetter,
  reset,
} = usePendingMove()

const code = route.params.code as string
const myRack = computed(() => store.myPlayer?.rack ?? [])
const myBoard = computed(() => store.game?.board ?? [])
const showThemePicker = ref(false)

const placedIndices = computed(() => {
  const s = new Set<number>()
  for (const g of ghosts.value.values()) {
    s.add(g.rackIndex)
  }
  return s
})

function handlePlaceTile(row: number, col: number) {
  tryPlaceTile(row, col, myRack.value)
}

async function handleSubmit() {
  const payload = buildMovePayload(myRack.value)
  if (!payload) return
  try {
    await store.submitMove(code, payload)
    clearAll()
  } catch (err) {
    store.addToast(String(err), 'error')
  }
}

function handleLeave() {
  reset()
  store.disconnectSSE()
  store.reset()
  router.push('/')
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-neutral-900 text-white">
    <header class="relative flex items-center justify-between border-b border-neutral-700 px-6 py-3">
      <span class="text-lg font-bold">Game {{ code }}</span>
      <div class="flex items-center gap-2">
        <button
          class="rounded px-2 py-1 text-xs text-neutral-400 transition hover:text-white"
          :title="`Theme: ${themeName}`"
          @click="showThemePicker = !showThemePicker"
        >
          Theme
        </button>
        <button
          class="rounded bg-red-700 px-3 py-1 text-sm transition hover:bg-red-800"
          @click="handleLeave"
        >
          Leave
        </button>
        <ThemePicker
          :themes="availableThemes"
          :current="themeName"
          :open="showThemePicker"
          @select="(name) => { setTheme(name); showThemePicker = false }"
          @close="showThemePicker = false"
        />
      </div>
    </header>

    <div class="flex flex-1 flex-col items-center gap-6 p-6 lg:flex-row lg:items-start lg:justify-center">
      <PlayerPanel
        :player="store.opponent"
        position="top"
      />

      <div class="flex flex-col items-center gap-4">
        <GameBoard
          :board="myBoard"
          :ghost-at="ghostAt"
          :blank-letter-at="(r, c) => blankLetterMap.get(`${r},${c}`)"
          :has-selection="selectedRackIndex !== null"
          :theme-name="themeName"
          @place-tile="handlePlaceTile"
          @remove-ghost="tryRemoveGhost"
          @set-blank-letter="setBlankLetter"
        />
        <TileRack
          :tiles="myRack"
          :selected-index="selectedRackIndex"
          :placed-indices="placedIndices"
          :swap-mode="swapMode"
          :swap-indices="swapIndices"
          @select-tile="selectRackTile"
        />
        <MoveControls
          v-if="store.isMyTurn && store.phase === 'playing'"
          :code="code"
          :has-placements="hasPendingPlacements"
          :has-swaps="hasSwapSelection"
          :swap-mode="swapMode"
          @submit="handleSubmit"
          @clear="clearAll"
          @toggle-swap="toggleSwapMode"
        />
      </div>

      <PlayerPanel
        :player="store.myPlayer"
        position="bottom"
      />
    </div>
  </div>
</template>
