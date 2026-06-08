<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { usePendingMove } from '../composables/usePendingMove'
import GameBoard from '../components/game/GameBoard.vue'
import TileRack from '../components/game/TileRack.vue'
import PlayerPanel from '../components/ui/PlayerPanel.vue'
import MoveControls from '../components/ui/MoveControls.vue'
import BoardBanner from '../components/ui/BoardBanner.vue'
import GameOverCard from '../components/ui/GameOverCard.vue'
import GamePausedCard from '../components/ui/GamePausedCard.vue'
import MoveHistorySidebar from '../components/ui/MoveHistorySidebar.vue'
import bagImg from '../assets/bag.svg'
import { useTheme } from '../composables/useTheme'

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

const { theme, toggle } = useTheme()
const code = route.params.code as string
const submitting = ref(false)
const historyOpen = ref(false)
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
    console.error('[Lexi] submit move failed', err)
    store.addToast(err instanceof Error ? err.message : String(err), 'error')
  } finally {
    submitting.value = false
  }
}

async function handlePass() {
  try {
    await store.submitMove(code, { type: 'pass' })
  } catch (err) {
    console.error('[Lexi] pass failed', err)
    store.addToast(err instanceof Error ? err.message : String(err), 'error')
  }
}

async function handleForfeit() {
  try {
    await store.forfeit(code)
  } catch (err) {
    console.error('[Lexi] forfeit failed', err)
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
  <div class="flex min-h-screen flex-col bg-lexi-bg text-lexi-text">
    <header class="flex items-center justify-between px-6 py-3 bg-lexi-header border-b-2 border-lexi-header-border">
      <!-- Game code copy -->
      <button
        class="flex items-center gap-1.5 px-2 py-1 font-lexi-ui text-lexi-xs font-bold tracking-lexi-wide text-lexi-text-secondary uppercase cursor-pointer transition-colors duration-lexi-fast hover:text-lexi-text"
        title="Copy room code"
        @click="copyCode"
      >
        GAME · {{ code }}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      </button>

      <div class="flex items-center gap-2">
        <!-- Theme toggle -->
        <button
          class="w-8 h-8 flex items-center justify-center text-lexi-text-secondary cursor-pointer transition-colors duration-lexi-fast hover:text-lexi-text"
          :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggle"
        >
          <svg v-if="theme === 'dark'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>

        <!-- History button -->
        <button
          class="px-3 py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-text-secondary border-lexi border-lexi-border-muted shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:text-lexi-text hover:border-lexi-border hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
          @click="historyOpen = true"
        >
          HISTORY
        </button>

        <!-- Leave button -->
        <button
          class="px-3 py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-danger border-lexi border-lexi-danger shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
          @click="handleLeave"
        >
          LEAVE
        </button>
      </div>
    </header>

    <div class="flex flex-1 flex-col items-center gap-6 p-6 pb-20 lg:flex-row lg:items-start lg:justify-center">
      <PlayerPanel
        :player="store.opponent"
        :is-active-turn="!store.isMyTurn && store.phase === 'playing'"
        :connected="store.connected"
        :avatar-key="store.opponent?.avatar"
        position="top"
      />

      <div class="flex flex-col items-center gap-4">
        <div class="flex items-center gap-1.5 self-end px-3 py-1 bg-lexi-bg-sunken border-lexi-light border-lexi-border">
          <img :src="bagImg" class="w-4 h-4" alt="bag" />
          <span class="font-lexi-numeric text-lexi-xs font-bold text-lexi-text lexi-numeric">
            {{ store.game?.bag_size ?? 0 }}
          </span>
        </div>

        <BoardBanner />

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
        :connected="store.myPlayer?.connected ?? true"
        :avatar-key="store.session?.avatar"
        position="bottom"
      />
    </div>

    <GamePausedCard
      v-if="store.phase === 'paused'"
      :players="store.game?.players ?? []"
      @leave="handleLeave"
    />

    <GameOverCard
      v-if="store.phase === 'finished'"
      :i-am-winner="iAmWinner"
      :end-reason="endReason"
      :winner="winner"
      :players="store.game?.players ?? []"
      @play-again="handlePlayAgain"
    />

    <MoveHistorySidebar
      :open="historyOpen"
      :moves="store.game?.move_history ?? []"
      :players="store.game?.players ?? []"
      :my-player-id="store.session?.player_id ?? ''"
      @close="historyOpen = false"
    />
  </div>
</template>
