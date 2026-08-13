<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { PREMIUM_LAYOUT, PREMIUM_LABELS } from '../../constants/board'

const props = defineProps<{
  board: (string | null)[][]
  ghostAt: (row: number, col: number) => { rackIndex: number; row: number; col: number } | undefined
  ghostLetterAt: (row: number, col: number) => string | undefined
  hasSelection: boolean
}>()

const emit = defineEmits<{
  placeTile: [row: number, col: number]
  removeGhost: [row: number, col: number]
  setBlankLetter: [row: number, col: number, letter: string]
}>()

const COL_LABELS = 'ABCDEFGHIJKLMNO'.split('')
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

const TILE_POINTS: Record<string, number> = {
  A: 1, B: 3, C: 3, D: 2, E: 1, F: 4, G: 2, H: 4, I: 1,
  J: 8, K: 5, L: 1, M: 3, N: 1, O: 1, P: 3, Q: 10, R: 1,
  S: 1, T: 1, U: 1, V: 4, W: 4, X: 8, Y: 4, Z: 10,
}

// Lowercase letters on the board are blanks played as that letter → 0 pts
function boardTilePts(letter: string | null): number {
  if (!letter) return 0
  if (letter !== letter.toUpperCase()) return 0
  return TILE_POINTS[letter] ?? 0
}

const pickerPos = ref<{ row: number; col: number } | null>(null)

function handleCellClick(row: number, col: number) {
  const ghost = props.ghostAt(row, col)
  if (ghost) {
    if (props.ghostLetterAt(row, col) === undefined) {
      pickerPos.value = { row, col }
    } else {
      emit('removeGhost', row, col)
    }
    return
  }
  if (props.hasSelection && !props.board[row]?.[col]) {
    emit('placeTile', row, col)
    // Auto-show blank picker if the placed tile is a blank (no letter yet)
    nextTick(() => {
      if (props.ghostAt(row, col) && props.ghostLetterAt(row, col) === undefined) {
        pickerPos.value = { row, col }
      }
    })
  }
}

function pickLetter(letter: string) {
  if (!pickerPos.value) return
  emit('setBlankLetter', pickerPos.value.row, pickerPos.value.col, letter)
  pickerPos.value = null
}

function premium(row: number, col: number) {
  return PREMIUM_LAYOUT[row][col]
}
</script>

<template>
  <div class="relative w-full overflow-x-auto">
    <div class="board-container">

      <div class="label-row">
        <div class="label-spacer" />
        <div v-for="(label, ci) in COL_LABELS" :key="ci" class="col-label">{{ label }}</div>
        <div class="label-spacer" />
      </div>

      <div class="board-middle">
        <div class="row-labels">
          <div v-for="(_, ri) in board" :key="ri" class="row-label">{{ ri + 1 }}</div>
        </div>

        <div class="board-grid">
          <template v-for="(row, ri) in board" :key="ri">
            <div
              v-for="(_, ci) in row"
              :key="ci"
              class="cell"
              :class="{
                'cell--occupied': board[ri]?.[ci],
                'cell--ghost': ghostAt(ri, ci),
                'cell--hoverable': hasSelection && !board[ri]?.[ci] && !ghostAt(ri, ci),
                [`cell--${premium(ri, ci)}`]: !board[ri]?.[ci] && !ghostAt(ri, ci) && premium(ri, ci) !== 'normal',
              }"
              @click="handleCellClick(ri, ci)"
            >
              <template v-if="board[ri]?.[ci]">
                <span class="tile-letter">{{ board[ri][ci]!.toUpperCase() }}</span>
                <span class="tile-pts">{{ boardTilePts(board[ri][ci]) }}</span>
              </template>
              <template v-else-if="ghostAt(ri, ci)">
                <span class="ghost-letter">{{ ghostLetterAt(ri, ci) ?? '?' }}</span>
              </template>
              <span v-else-if="premium(ri, ci) !== 'normal'" class="premium-label">
                {{ PREMIUM_LABELS[premium(ri, ci)] }}
              </span>
            </div>
          </template>
        </div>

        <div class="row-labels">
          <div v-for="(_, ri) in board" :key="ri" class="row-label">{{ ri + 1 }}</div>
        </div>
      </div>

      <div class="label-row">
        <div class="label-spacer" />
        <div v-for="(label, ci) in COL_LABELS" :key="ci" class="col-label">{{ label }}</div>
        <div class="label-spacer" />
      </div>
    </div>

    <div
      v-if="!board.length"
      class="absolute inset-0 flex items-center justify-center font-lexi-ui text-lexi-xs text-lexi-text-secondary"
    >
      Loading board…
    </div>

    <div v-if="pickerPos" class="blank-picker">
      <div class="blank-picker__title">Choose letter for blank</div>
      <div class="blank-picker__grid">
        <button v-for="letter in LETTERS" :key="letter" class="blank-picker__btn" @click="pickLetter(letter)">
          {{ letter }}
        </button>
      </div>
      <button class="blank-picker__cancel" @click="pickerPos = null">Cancel</button>
    </div>
  </div>
</template>

<style scoped>
.board-container {
  /* Fluid board: shrinks continuously down to a legible/tappable floor on
     narrow phones instead of overflowing. The 58px covers everything between
     the viewport edge and a grid cell: GameView's own p-3 padding (24px),
     this container's padding+border (20px), and the 14 1px grid gaps. */
  --board-label: clamp(14px, 4.5vw, 24px);
  --board-cell: clamp(18px, calc((100vw - 2 * var(--board-label) - 58px) / 15), 34px);
  display: inline-block;
  border: 2px solid var(--color-board-border);
  padding: 8px;
  background: var(--color-board-bg);
  box-shadow: var(--shadow-md);
}

.label-row {
  display: flex;
  align-items: center;
  height: 20px;
}

.label-spacer {
  width: var(--board-label);
  flex-shrink: 0;
}

.col-label {
  width: var(--board-cell);
  text-align: center;
  font-family: var(--font-ui);
  font-size: clamp(9px, calc(var(--board-label) * 0.5), 11px);
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-text-secondary);
}

.board-middle {
  display: flex;
  align-items: stretch;
}

.row-labels {
  width: var(--board-label);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.row-label {
  height: var(--board-cell);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-ui);
  font-size: clamp(9px, calc(var(--board-label) * 0.5), 11px);
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-text-secondary);
}

.board-grid {
  display: grid;
  grid-template-columns: repeat(15, var(--board-cell));
  grid-template-rows: repeat(15, var(--board-cell));
  gap: 1px;
  background-color: var(--color-board-gridline);
  overflow: hidden;
}

.cell {
  width: var(--board-cell);
  height: var(--board-cell);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: default;
  background: var(--color-cell-empty-bg);
  transition: background 0.12s, box-shadow 0.12s;
}

.cell--hoverable {
  cursor: pointer;
}
.cell--hoverable:hover {
  background: var(--color-bg-elevated);
  box-shadow: inset 0 0 0 2px var(--color-border);
}

.cell--occupied {
  background: var(--color-tile-placed-bg);
}

.tile-letter {
  font-family: var(--font-display);
  font-size: clamp(11px, calc(var(--board-cell) * 0.5), 18px);
  font-weight: 600;
  color: var(--color-tile-placed-text);
}

.tile-pts {
  position: absolute;
  bottom: 2px;
  right: 3px;
  font-family: var(--font-ui);
  font-size: clamp(5px, calc(var(--board-cell) * 0.2), 7px);
  font-weight: 700;
  line-height: 1;
  color: var(--color-tile-placed-points);
}

.cell--ghost {
  background: var(--color-active-highlight-subtle);
  box-shadow: inset 0 0 0 2px var(--color-active-highlight);
}

.ghost-letter {
  font-family: var(--font-display);
  font-size: clamp(11px, calc(var(--board-cell) * 0.5), 18px);
  font-weight: 600;
  color: var(--color-active-highlight);
}

.cell--dl     { background: var(--color-sq-dl-bg); }
.cell--tl     { background: var(--color-sq-tl-bg); }
.cell--dw     { background: var(--color-sq-dw-bg); }
.cell--tw     { background: var(--color-sq-tw-bg); }
.cell--center { background: var(--color-sq-star-bg); }

.premium-label {
  font-family: var(--font-ui);
  font-size: clamp(6px, calc(var(--board-cell) * 0.24), 8px);
  font-weight: 700;
  letter-spacing: 0.1em;
}

.cell--dl     .premium-label { color: var(--color-sq-dl-label); }
.cell--tl     .premium-label { color: var(--color-sq-tl-label); }
.cell--dw     .premium-label { color: var(--color-sq-dw-label); }
.cell--tw     .premium-label { color: var(--color-sq-tw-label); }
.cell--center .premium-label { color: var(--color-sq-star-label); }

.blank-picker {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 10;
  transform: translate(-50%, -50%);
  border: 2px solid var(--color-border);
  background: var(--color-bg-elevated);
  box-shadow: var(--shadow-md);
  padding: 12px;
}

.blank-picker__title {
  margin-bottom: 8px;
  text-align: center;
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary);
}

.blank-picker__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.blank-picker__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--color-tile-bg);
  color: var(--color-tile-text);
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 700;
  border: 1px solid var(--color-tile-border);
  cursor: pointer;
  transition: all 0.12s;
}

.blank-picker__btn:hover {
  background: var(--color-tile-selected-bg);
  border-color: var(--color-tile-selected-border);
  color: var(--color-tile-selected-text);
}

.blank-picker__cancel {
  margin-top: 8px;
  width: 100%;
  background: transparent;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 8px;
  border: 1px solid var(--color-border-muted);
  cursor: pointer;
  transition: all 0.12s;
}

.blank-picker__cancel:hover {
  border-color: var(--color-border);
  color: var(--color-text-primary);
}
</style>
