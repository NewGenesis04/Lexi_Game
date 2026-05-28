<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { usePendingMove } from '../composables/usePendingMove'
import GameBoard from '../components/game/GameBoard.vue'
import TileRack from '../components/game/TileRack.vue'
import PlayerPanel from '../components/ui/PlayerPanel.vue'
import MoveControls from '../components/ui/MoveControls.vue'
import bagImg from '../assets/bag.svg'

const route = useRoute()
const router = useRouter()
const store = useGameStore()
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
const myBoard = computed<(string | null)[][]>(() => store.game?.board ?? [])

const placedIndices = computed(() => {
  const s = new Set<number>()
  for (const g of ghosts.value.values()) {
    s.add(g.rackIndex)
  }
  return s
})

const winner = computed(() => {
  if (!store.game || store.game.phase !== 'finished') return null
  const sorted = [...store.game.players].sort((a, b) => b.score - a.score)
  return sorted[0] ?? null
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

async function handlePass() {
  try {
    await store.submitMove(code, { type: 'pass' })
  } catch (err) {
    store.addToast(String(err), 'error')
  }
}

async function handleForfeit() {
  try {
    await store.forfeit(code)
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
  <div class="flex min-h-screen flex-col" style="background: var(--color-surface); color: var(--color-on-surface);">
    <header
      class="flex items-center justify-between px-6 py-3"
      style="background: var(--color-surface-container-low); border-bottom: 1px solid var(--color-outline-variant);"
    >
      <span style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: var(--color-on-surface-variant);">
        GAME · {{ code }}
      </span>
      <div class="flex items-center gap-2">
        <button
          style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: var(--color-on-primary); background: var(--color-tertiary-container); border: none; border-radius: 0.25rem; padding: 6px 12px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.3); transition: all 0.2s;"
          @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
          @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
          @click="handleLeave"
        >
          Leave
        </button>
      </div>
    </header>

    <div class="flex flex-1 flex-col items-center gap-6 p-6 lg:flex-row lg:items-start lg:justify-center" style="padding-bottom: 80px;">
      <PlayerPanel
        :player="store.opponent"
        :is-active-turn="!store.isMyTurn && store.phase === 'playing'"
        :connected="store.connected"
        position="top"
      />

      <div class="flex flex-col items-center gap-4">
        <div
          class="flex items-center gap-1.5 self-end"
          style="
            background: rgba(38,38,38,0.4);
            border-radius: 999px;
            border: 1px solid rgba(96,96,96,0.3);
            padding: 4px 12px;
          "
        >
          <img :src="bagImg" style="width: 16px; height: 16px;" alt="bag" />
          <span style="font-family: var(--font-panel); font-size: 12px; font-weight: 700; color: #d4d4d4;">
            {{ store.game?.bag_size ?? 0 }}
          </span>
        </div>

        <GameBoard
          :board="myBoard"
          :ghost-at="ghostAt"
          :blank-letter-at="(r, c) => blankLetterMap.get(`${r},${c}`)"
          :has-selection="selectedRackIndex !== null"
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
          @pass="handlePass"
          @forfeit="handleForfeit"
        />
      </div>

      <PlayerPanel
        :player="store.myPlayer"
        :is-active-turn="store.isMyTurn && store.phase === 'playing'"
        :connected="true"
        position="bottom"
      />
    </div>

    <div
      v-if="store.phase === 'finished'"
      class="fixed inset-0 z-50 flex items-center justify-center"
      style="background: rgba(19,19,19,0.9);"
    >
      <div
        class="text-center"
        style="
          background: var(--color-surface-container-low);
          border-radius: 0.5rem;
          border: 1px solid var(--color-outline);
          box-shadow: var(--shadow-overlay);
          padding: 32px;
          max-width: 360px;
          width: 100%;
        "
      >
        <h2 style="font-family: var(--font-serif); font-size: 32px; font-weight: 600; color: var(--color-on-surface-variant); letter-spacing: -0.02em; margin-bottom: 24px;">
          GAME OVER
        </h2>

        <div v-if="winner" class="space-y-1">
          <div style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: var(--color-on-surface-variant);">Winner</div>
          <div style="font-family: var(--font-serif); font-size: 28px; font-weight: 500; color: var(--color-primary);">{{ winner.nickname }}</div>
          <div style="font-family: var(--font-sans); font-size: 36px; font-weight: 600; color: var(--color-on-surface);">{{ winner.score }}</div>
        </div>

        <div v-if="store.game" class="space-y-2 mt-6">
          <div style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: var(--color-on-surface-variant);">Final Scores</div>
          <div class="space-y-2">
            <div
              v-for="(p, i) in store.game.players"
              :key="i"
              class="flex items-center justify-between"
              :style="{
                background: 'var(--color-surface-container)',
                borderRadius: '0.375rem',
                border: '1px solid var(--color-outline-variant)',
                padding: '12px 16px',
              }"
            >
              <span style="font-family: var(--font-serif); font-size: 18px; color: var(--color-on-surface);">{{ p.nickname }}</span>
              <span style="font-family: var(--font-sans); font-size: 24px; font-weight: 600; color: winner?.id === p.id ? 'var(--color-primary)' : 'var(--color-tertiary)';">{{ p.score }}</span>
            </div>
          </div>
        </div>

        <button
          class="w-full mt-6"
          style="
            background: linear-gradient(180deg, var(--color-outline), #8a7d7b);
            color: var(--color-surface-container-lowest);
            border: none;
            box-shadow: var(--shadow-button-filled);
            border-radius: 0.25rem;
            padding: 12px 24px;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            cursor: pointer;
            transition: all 0.2s;
          "
          @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
          @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
          @click="router.push('/')"
        >
          Play Again
        </button>
      </div>
    </div>
  </div>
</template>
