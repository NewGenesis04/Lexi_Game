<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { usePendingMove } from '../composables/usePendingMove'
import GameBoard from '../components/game/GameBoard.vue'
import TileRack from '../components/game/TileRack.vue'
import PlayerPanel from '../components/ui/PlayerPanel.vue'
import PlayerMini from '../components/ui/PlayerMini.vue'
import MoveControls from '../components/ui/MoveControls.vue'
import BoardBanner from '../components/ui/BoardBanner.vue'
import GameOverCard from '../components/ui/GameOverCard.vue'
import GamePausedCard from '../components/ui/GamePausedCard.vue'
import LeaveConfirmCard from '../components/ui/LeaveConfirmCard.vue'
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
const showLeaveConfirm = ref(false)
const resultsOpen = ref(true)
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
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(code)
    } else {
      // navigator.clipboard requires a secure context (HTTPS or localhost) —
      // unavailable e.g. testing over plain HTTP via a LAN IP. Fall back to
      // the legacy execCommand path, which still works there.
      const textarea = document.createElement('textarea')
      textarea.value = code
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      const copied = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!copied) throw new Error('execCommand copy failed')
    }
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
  if (isDraw.value) return null
  return [...store.game.players].sort((a, b) => b.score - a.score)[0] ?? null
})

const isDraw = computed(() =>
  store.game?.phase === 'finished' &&
  endReason.value === 'normal' &&
  store.game.players.length === 2 &&
  store.game.players[0].score === store.game.players[1].score
)

const iAmWinner = computed(() => winner.value?.id === store.session?.player_id)

const opponentNickname = computed(() => store.opponent?.nickname ?? 'opponent')

const endReason = computed<'forfeit' | 'timeout' | 'normal'>(() => {
  const t = store.game?.last_move?.type
  if (t === 'forfeit') return 'forfeit'
  if (t === 'timeout') return 'timeout'
  return 'normal'
})

function handlePlaceTile(row: number, col: number) {
  if (store.phase !== 'playing') return
  tryPlaceTile(row, col, myRack.value)
}

function handleSelectTile(index: number) {
  if (store.phase !== 'playing') return
  selectRackTile(index)
}

function handleRemoveGhost(row: number, col: number) {
  if (store.phase !== 'playing') return
  tryRemoveGhost(row, col)
}

function handleSetBlankLetter(row: number, col: number, letter: string) {
  if (store.phase !== 'playing') return
  setBlankLetter(row, col, letter)
}

watch(
  () => store.phase,
  (phase) => {
    if (phase === 'finished') reset()
  },
)

async function handleSubmit() {
  const payload = buildMovePayload(myRack.value)
  if (!payload) return
  submitting.value = true
  try {
    await store.submitMove(code, payload)
    reset()
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
  showLeaveConfirm.value = false
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
  <div class="flex min-h-dvh flex-col bg-lexi-bg text-lexi-text">
    <header class="flex items-center justify-between px-2 py-1.5 lg:px-6 lg:py-3 bg-lexi-header border-b-2 border-lexi-header-border">
      <!-- Game code copy -->
      <button
        class="flex items-center gap-1 lg:gap-1.5 px-1.5 py-1 lg:px-2 font-lexi-ui text-lexi-xs font-bold tracking-lexi-wide text-lexi-text-secondary uppercase cursor-pointer transition-colors duration-lexi-fast hover:text-lexi-text"
        title="Copy room code"
        @click="copyCode"
      >
        GAME · {{ code }}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      </button>

      <div class="flex items-center gap-1 lg:gap-2">
        <!-- Theme toggle -->
        <button
          class="w-7 h-7 lg:w-8 lg:h-8 flex items-center justify-center text-lexi-text-secondary cursor-pointer transition-colors duration-lexi-fast hover:text-lexi-text"
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

        <!-- Rules link (opens in a new tab) -->
        <a
          href="/rules"
          target="_blank"
          rel="noopener"
          class="px-2 py-1 lg:px-3 lg:py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-text-secondary border-lexi border-lexi-border-muted shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:text-lexi-text hover:border-lexi-border hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
        >
          RULES
        </a>

        <!-- Result button (re-open the finished card after dismissing) -->
        <button
          v-if="store.phase === 'finished' && !resultsOpen"
          class="px-2 py-1 lg:px-3 lg:py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-text-secondary border-lexi border-lexi-border-muted shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:text-lexi-text hover:border-lexi-border hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
          @click="resultsOpen = true"
        >
          RESULT
        </button>

        <!-- History button -->
        <button
          class="px-2 py-1 lg:px-3 lg:py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-text-secondary border-lexi border-lexi-border-muted shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:text-lexi-text hover:border-lexi-border hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
          @click="historyOpen = true"
        >
          HISTORY
        </button>

        <!-- Leave button -->
        <button
          class="px-2 py-1 lg:px-3 lg:py-1.5 font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase text-lexi-danger border-lexi border-lexi-danger shadow-lexi-sm cursor-pointer transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5"
          @click="showLeaveConfirm = true"
        >
          LEAVE
        </button>
      </div>
    </header>

    <!-- Combined player header (mobile only) — flat horizontal strip so both
         players' score/clock are visible without pushing the board below the fold. -->
    <div class="flex lg:hidden w-full items-center justify-between gap-2 px-3 py-2 bg-lexi-header border-b-2 border-lexi-header-border">
      <PlayerMini
        :player="store.opponent"
        align="left"
        :is-active-turn="!store.isMyTurn && store.phase === 'playing'"
        :connected="store.connected"
        :avatar-key="store.opponent?.avatar"
      />
      <div class="flex flex-shrink-0 items-center gap-1 px-2 py-1 bg-lexi-bg-sunken border-lexi-light border-lexi-border">
        <img :src="bagImg" class="w-3.5 h-3.5" alt="bag" />
        <span class="font-lexi-numeric text-lexi-xs font-bold text-lexi-text lexi-numeric">
          {{ store.game?.bag_size ?? 0 }}
        </span>
      </div>
      <PlayerMini
        :player="store.myPlayer"
        align="right"
        :is-active-turn="store.isMyTurn && store.phase === 'playing'"
        :connected="store.myPlayer?.connected ?? true"
        :avatar-key="store.session?.avatar"
      />
    </div>

    <div class="flex flex-1 flex-col items-center gap-3 p-3 pb-[max(24px,env(safe-area-inset-bottom))] lg:flex-row lg:items-start lg:justify-center lg:gap-6 lg:p-6 lg:pb-20">
      <PlayerPanel
        class="hidden lg:block"
        :player="store.opponent"
        :is-active-turn="!store.isMyTurn && store.phase === 'playing'"
        :connected="store.connected"
        :avatar-key="store.opponent?.avatar"
        position="top"
      />

      <div class="flex flex-1 flex-col items-center justify-between gap-2 lg:flex-none lg:justify-start lg:gap-4">
        <div class="hidden lg:flex items-center gap-1.5 self-end px-3 py-1 bg-lexi-bg-sunken border-lexi-light border-lexi-border">
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
          @remove-ghost="handleRemoveGhost"
          @set-blank-letter="handleSetBlankLetter"
        />
        <TileRack
          :tiles="myRack"
          :selected-index="selectedRackIndex"
          :placed-indices="placedIndices"
          :swap-mode="swapMode"
          :swap-indices="swapIndices"
          @select-tile="handleSelectTile"
        />
        <MoveControls
          v-if="store.isMyTurn && store.phase === 'playing'"
          class="w-full sticky bottom-0 z-10 bg-lexi-bg border-t-2 border-lexi-border-muted pt-2 pb-[max(16px,env(safe-area-inset-bottom))] lg:static lg:w-auto lg:bg-transparent lg:border-t-0 lg:pt-0 lg:pb-0"
          :code="code"
          :has-placements="hasPendingPlacements"
          :has-swaps="hasSwapSelection"
          :swap-mode="swapMode"
          :loading="submitting"
          :bag-size="store.game?.bag_size ?? 0"
          @submit="handleSubmit"
          @clear="clearAll"
          @toggle-swap="toggleSwapMode"
          @pass="handlePass"
          @forfeit="handleForfeit"
        />
      </div>

      <PlayerPanel
        class="hidden lg:block"
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
      v-if="store.phase === 'finished' && resultsOpen"
      :i-am-winner="iAmWinner"
      :end-reason="endReason"
      :winner="winner"
      :draw="isDraw"
      :players="store.game?.players ?? []"
      @play-again="handlePlayAgain"
      @dismiss="resultsOpen = false"
    />

    <LeaveConfirmCard
      v-if="showLeaveConfirm && store.phase === 'playing'"
      :opponent-nickname="opponentNickname"
      @confirm="handleLeave"
      @cancel="showLeaveConfirm = false"
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
