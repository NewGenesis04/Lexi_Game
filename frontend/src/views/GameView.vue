<script setup lang="ts">
import { computed, ref } from 'vue'
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
const submitting = ref(false)
const myRack = computed(() => store.myPlayer?.rack ?? [])
const myBoard = computed<(string | null)[][]>(() => store.game?.board ?? [])

function ghostLetterAt(r: number, c: number): string | undefined {
  const ghost = ghostAt(r, c)
  if (!ghost) return undefined
  const tile = myRack.value[ghost.rackIndex]
  if (!tile) return undefined
  if (tile.letter === ' ') return blankLetterMap.value.get(`${r},${c}`)
  return tile.letter
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(code)
    store.addToast(`Code copied: ${code}`, 'info')
  } catch {
    store.addToast('Failed to copy room code', 'error')
  }
}

const placedIndices = computed(() => {
  const s = new Set<number>()
  for (const g of ghosts.value.values()) {
    s.add(g.rackIndex)
  }
  return s
})

const winner = computed(() => {
  if (!store.game || store.game.phase !== 'finished') return null
  const last = store.game.last_move
  if (last?.type === 'forfeit' || last?.type === 'timeout') {
    return store.game.players.find(p => p.id !== last.player_id) ?? null
  }
  return [...store.game.players].sort((a, b) => b.score - a.score)[0] ?? null
})

const iAmWinner = computed(() => winner.value?.id === store.session?.player_id)

const endReason = computed<'forfeit' | 'timeout' | 'normal'>(() => {
  const t = store.game?.last_move?.type
  if (t === 'forfeit') return 'forfeit'
  if (t === 'timeout') return 'timeout'
  return 'normal'
})

function handlePlaceTile(row: number, col: number) {
  tryPlaceTile(row, col, myRack.value)
}

async function handleSubmit() {
  const payload = buildMovePayload(myRack.value)
  if (!payload) return
  submitting.value = true
  try {
    await store.submitMove(code, payload)
    clearAll()
  } catch (err) {
    store.addToast(err instanceof Error ? err.message : String(err), 'error')
  } finally {
    submitting.value = false
  }
}

async function handlePass() {
  try {
    await store.submitMove(code, { type: 'pass' })
  } catch (err) {
    store.addToast(err instanceof Error ? err.message : String(err), 'error')
  }
}

async function handleForfeit() {
  try {
    await store.forfeit(code)
  } catch (err) {
    store.addToast(err instanceof Error ? err.message : String(err), 'error')
  }
}

async function handleLeave() {
  if (store.phase === 'playing') {
    try {
      await store.forfeit(code)
    } catch {
      // game may already be over — proceed with cleanup regardless
    }
  }
  reset()
  store.disconnectSSE()
  store.reset()
  router.push('/')
}

function handlePlayAgain() {
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
      <button
        style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: var(--color-on-surface-variant); background: none; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 0.25rem; transition: background 0.15s;"
        @mouseenter="(e: any) => { e.currentTarget.style.background = 'var(--color-surface-container)' }"
        @mouseleave="(e: any) => { e.currentTarget.style.background = 'none' }"
        @click="copyCode"
        title="Copy room code"
      >
        GAME · {{ code }}
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      </button>
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
          :ghost-letter-at="ghostLetterAt"
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
          :loading="submitting"
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
        <div style="margin-bottom: 6px;">
          <h2 :style="{
            fontFamily: 'var(--font-serif)',
            fontSize: '36px',
            fontWeight: 600,
            letterSpacing: '-0.02em',
            lineHeight: '1.1',
            color: endReason === 'timeout' ? '#f59e0b' : iAmWinner ? 'var(--color-primary)' : 'var(--color-tertiary)',
          }">
            {{ endReason === 'timeout' ? (iAmWinner ? 'YOU WON' : 'TIMED OUT') : (iAmWinner ? 'YOU WON' : 'YOU LOST') }}
          </h2>
          <p :style="{
            fontFamily: 'var(--font-sans)',
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.12em',
            marginTop: '4px',
            color: endReason === 'timeout' ? '#f59e0b' : endReason === 'forfeit' ? 'var(--color-tertiary)' : 'var(--color-on-surface-variant)',
          }">
            {{ endReason === 'timeout' ? 'TIME OUT' : endReason === 'forfeit' ? 'FORFEITED' : 'GAME OVER' }}
          </p>
        </div>

        <div v-if="winner" style="margin-bottom: 4px;">
          <div style="font-family: var(--font-sans); font-size: 10px; font-weight: 700; letter-spacing: 0.12em; color: var(--color-on-surface-variant); margin-bottom: 2px;">
            {{ iAmWinner ? 'YOUR SCORE' : 'WINNER' }}
          </div>
          <div style="font-family: var(--font-serif); font-size: 22px; font-weight: 500; color: var(--color-primary);">
            {{ iAmWinner ? '' : winner.nickname + ' · ' }}{{ winner.score }} pts
          </div>
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
          @click="handlePlayAgain"
        >
          Play Again
        </button>
      </div>
    </div>
  </div>
</template>
