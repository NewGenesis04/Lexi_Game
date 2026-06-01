<script setup lang="ts">
import { ref } from 'vue'
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
  <div class="relative">
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
      class="absolute inset-0 flex items-center justify-center"
      style="color: var(--color-on-surface-variant); font-family: var(--font-sans); font-size: 12px;"
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
  display: inline-block;
  border-radius: var(--radius-board);
  border: 2px solid var(--color-outline);
  padding: 8px;
  background: linear-gradient(180deg, var(--color-surface-dim), var(--color-surface-container-low));
  box-shadow: var(--shadow-board);
}

.label-row {
  display: flex;
  align-items: center;
  height: 20px;
}

.label-spacer {
  width: 24px;
  flex-shrink: 0;
}

.col-label {
  width: 34px;
  text-align: center;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}

.board-middle {
  display: flex;
  align-items: stretch;
}

.row-labels {
  width: 24px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.row-label {
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}

.board-grid {
  display: grid;
  grid-template-columns: repeat(15, 34px);
  grid-template-rows: repeat(15, 34px);
  gap: 1px;
  background-color: var(--color-outline-variant);
  border-radius: var(--radius-board);
  overflow: hidden;
}

.cell {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: default;
  background: var(--color-surface-container-low);
  transition: background 0.12s, box-shadow 0.12s;
}

.cell--hoverable {
  cursor: pointer;
}
.cell--hoverable:hover {
  background: var(--color-surface-container);
  box-shadow: inset 0 0 0 1px var(--color-outline);
}

.cell--occupied {
  background: var(--color-placed-tile-bg);
  box-shadow: var(--shadow-cell-occupied);
}

.tile-letter {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-placed-tile-letter);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
}

.tile-pts {
  position: absolute;
  bottom: 2px;
  right: 3px;
  font-family: var(--font-sans);
  font-size: 7px;
  font-weight: 700;
  line-height: 1;
  color: var(--color-placed-tile-points);
}

.cell--ghost {
  background: rgba(212, 197, 169, 0.35);
  box-shadow: inset 0 0 0 2px var(--color-active-turn), 0 0 8px rgba(16, 185, 129, 0.3);
}

.ghost-letter {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-active-turn);
}

.cell--dl     { background: var(--color-premium-dl-bg); }
.cell--tl     { background: var(--color-premium-tl-bg); }
.cell--dw     { background: var(--color-premium-dw-bg); }
.cell--tw     { background: var(--color-premium-tw-bg); }
.cell--center { background: var(--color-premium-center-bg); }

.premium-label {
  font-family: var(--font-sans);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.cell--dl     .premium-label { color: var(--color-premium-dl-label); }
.cell--tl     .premium-label { color: var(--color-premium-tl-label); }
.cell--dw     .premium-label { color: var(--color-premium-dw-label); }
.cell--tw     .premium-label { color: var(--color-premium-tw-label); }
.cell--center .premium-label { color: var(--color-premium-center-label); }

.blank-picker {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 10;
  transform: translate(-50%, -50%);
  border-radius: 0.5rem;
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-low);
  box-shadow: var(--shadow-overlay);
  padding: 12px;
}

.blank-picker__title {
  margin-bottom: 8px;
  text-align: center;
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--color-on-surface-variant);
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
  border-radius: 0.25rem;
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.blank-picker__btn:hover {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.blank-picker__cancel {
  margin-top: 8px;
  width: 100%;
  border-radius: 0.25rem;
  background: var(--color-surface-container-high);
  color: var(--color-on-surface-variant);
  font-family: var(--font-sans);
  font-size: 11px;
  padding: 4px 8px;
  border: none;
  cursor: pointer;
}

.blank-picker__cancel:hover {
  color: var(--color-on-surface);
}
</style>
