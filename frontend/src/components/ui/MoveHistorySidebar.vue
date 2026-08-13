<script setup lang="ts">
import { computed } from 'vue'
import type { MoveOut, PlayerOut } from '../../types/game'

const props = defineProps<{
  open: boolean
  moves: MoveOut[]
  players: PlayerOut[]
  myPlayerId: string
}>()

const emit = defineEmits<{ close: [] }>()

const myPlayer = computed(() => props.players.find(p => p.id === props.myPlayerId) ?? null)
const opponent = computed(() => props.players.find(p => p.id !== props.myPlayerId) ?? null)

function isMyMove(move: MoveOut) {
  return move.player_id === props.myPlayerId
}

function playerName(move: MoveOut): string {
  return (props.players.find(p => p.id === move.player_id)?.nickname ?? '?').toUpperCase()
}

interface MoveDisplay { label: string; isPlace: boolean; crossCount: number }

function moveDisplay(move: MoveOut): MoveDisplay {
  if (move.type === 'place') {
    const primary = move.words[0] ?? '?'
    const crossCount = Math.max(0, move.words.length - 1)
    return { label: primary, isPlace: true, crossCount }
  }
  if (move.type === 'swap') return { label: `SWAP (${move.letters.length})`, isPlace: false, crossCount: 0 }
  if (move.type === 'pass') return { label: 'PASS', isPlace: false, crossCount: 0 }
  if (move.type === 'forfeit') return { label: 'FORFEIT', isPlace: false, crossCount: 0 }
  if (move.type === 'timeout') return { label: 'TIME OUT', isPlace: false, crossCount: 0 }
  return { label: '—', isPlace: false, crossCount: 0 }
}

const reversedMoves = computed(() => [...props.moves].reverse())
</script>

<template>
  <Transition name="scrim">
    <div
      v-if="open"
      class="fixed inset-0 z-40"
      style="background: rgba(0, 0, 0, 0.5);"
      @click="emit('close')"
    />
  </Transition>

  <Transition name="sidebar">
    <div v-if="open" class="sidebar">
      <!-- Header -->
      <div class="sidebar-header">
        <div class="sidebar-header__top">
          <span class="sidebar-title">MOVE HISTORY</span>
          <button class="sidebar-close" @click="emit('close')">✕</button>
        </div>
        <!-- Legend -->
        <div class="legend">
          <div class="legend-item">
            <div class="legend-swatch legend-swatch--mine" />
            <span class="legend-label">{{ myPlayer?.nickname ?? 'YOU' }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-swatch legend-swatch--opp" />
            <span class="legend-label">{{ opponent?.nickname ?? 'OPP' }}</span>
          </div>
        </div>
      </div>

      <!-- Move list -->
      <div class="move-list">
        <div
          v-for="(move, i) in reversedMoves"
          :key="i"
          class="move-row"
          :class="isMyMove(move) ? 'move-row--mine' : 'move-row--opp'"
        >
          <span class="move-player">{{ playerName(move) }}</span>
          <span class="move-sep">·</span>
          <span v-if="moveDisplay(move).isPlace" class="move-word">
            {{ moveDisplay(move).label }}<span v-if="moveDisplay(move).crossCount > 0" class="cross-count">+{{ moveDisplay(move).crossCount }}</span>
          </span>
          <span v-else class="move-action">{{ moveDisplay(move).label }}</span>
          <span class="move-sep">·</span>
          <span class="move-score" :class="move.score_delta > 0 ? 'move-score--positive' : 'move-score--zero'">
            {{ move.score_delta > 0 ? `+${move.score_delta}` : '—' }}
          </span>
        </div>

        <div v-if="!moves.length" class="move-empty">No moves yet</div>
      </div>

      <!-- Footer -->
      <div class="sidebar-footer">
        <span class="footer-count">{{ moves.length }} MOVES</span>
        <span class="footer-scores">
          {{ myPlayer?.nickname?.toUpperCase() ?? 'YOU' }} {{ myPlayer?.score ?? 0 }}
          &nbsp;·&nbsp;
          {{ opponent?.nickname?.toUpperCase() ?? 'OPP' }} {{ opponent?.score ?? 0 }}
        </span>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 50;
  width: min(85vw, 340px);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-elevated);
  border-right: 2px solid var(--color-border);
  box-shadow: var(--shadow-lg);
}

@media (min-width: 640px) {
  .sidebar {
    width: 260px;
  }
}

/* ── Header ── */
.sidebar-header {
  padding: 12px 14px 10px;
  border-bottom: 2px solid var(--color-border);
  flex-shrink: 0;
}
.sidebar-header__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.sidebar-title {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-secondary);
}
.sidebar-close {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color var(--transition-fast);
}
.sidebar-close:hover { color: var(--color-text-primary); }

/* ── Legend ── */
.legend {
  display: flex;
  align-items: center;
  gap: 14px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.legend-swatch {
  width: 10px;
  height: 10px;
  border: 1px solid var(--color-border-muted);
  flex-shrink: 0;
}
.legend-swatch--mine { background: var(--color-history-my-bg); }
.legend-swatch--opp  { background: var(--color-history-opp-bg); }
.legend-label {
  font-family: var(--font-ui);
  font-size: 10px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

/* ── Move list ── */
.move-list {
  flex: 1;
  overflow-y: auto;
}
.move-row {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid var(--color-border-muted);
  gap: 0;
}
.move-row--mine { background: var(--color-history-my-bg); }
.move-row--opp  { background: var(--color-history-opp-bg); }

.move-player {
  font-family: var(--font-ui);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  flex-shrink: 0;
  width: 42px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.move-sep {
  font-family: var(--font-ui);
  font-size: 10px;
  color: var(--color-border-muted);
  margin: 0 5px;
  flex-shrink: 0;
}
.move-word {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 500;
  color: var(--color-text-primary);
  line-height: 1.1;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.move-action {
  font-family: var(--font-ui);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  flex: 1;
  min-width: 0;
}
.move-score {
  font-family: var(--font-numeric);
  font-size: 11px;
  font-weight: 700;
  text-align: right;
  flex-shrink: 0;
  width: 34px;
  font-variant-numeric: tabular-nums;
}
.move-score--positive { color: var(--color-text-primary); }
.move-score--zero     { color: var(--color-text-muted); }

.cross-count {
  font-family: var(--font-ui);
  font-size: 8px;
  font-weight: 700;
  color: var(--color-text-muted);
  margin-left: 3px;
  vertical-align: super;
  letter-spacing: 0;
}

.move-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--color-text-muted);
}

/* ── Footer ── */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: 2px solid var(--color-border);
  flex-shrink: 0;
}
.footer-count {
  font-family: var(--font-ui);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-muted);
}
.footer-scores {
  font-family: var(--font-numeric);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

/* ── Transitions ── */
.sidebar-enter-active,
.sidebar-leave-active {
  transition: transform 200ms ease;
}
.sidebar-enter-from,
.sidebar-leave-to {
  transform: translateX(-100%);
}

.scrim-enter-active,
.scrim-leave-active {
  transition: opacity 200ms ease;
}
.scrim-enter-from,
.scrim-leave-to {
  opacity: 0;
}
</style>
