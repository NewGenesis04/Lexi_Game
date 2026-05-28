<script setup lang="ts">
import { ref } from 'vue'
import { PREMIUM_LAYOUT, PREMIUM_LABELS } from '../../constants/board'

const props = defineProps<{
  board: (string | null)[][]
  ghostAt: (row: number, col: number) => { rackIndex: number; row: number; col: number } | undefined
  blankLetterAt: (row: number, col: number) => string | undefined
  hasSelection: boolean
}>()

const emit = defineEmits<{
  placeTile: [row: number, col: number]
  removeGhost: [row: number, col: number]
  setBlankLetter: [row: number, col: number, letter: string]
}>()

const COL_LABELS = 'ABCDEFGHIJKLMNO'.split('')
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

const pickerPos = ref<{ row: number; col: number } | null>(null)

function handleCellClick(row: number, col: number) {
  const ghost = props.ghostAt(row, col)
  if (ghost) {
    const cell = props.board[row]?.[col]
    if (cell === ' ') {
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
      <table class="board-table">
        <thead>
          <tr>
            <th class="h-5 w-6" />
            <th v-for="(label, ci) in COL_LABELS" :key="ci" class="h-5 w-9 text-center label">
              {{ label }}
            </th>
            <th class="h-5 w-6" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ri) in board" :key="ri">
            <td class="w-6 text-center label">{{ ri + 1 }}</td>
            <td v-for="(_, ci) in row" :key="ci" class="p-[1px]">
              <div
                class="cell"
                :class="{
                  'cell--occupied': board[ri]?.[ci],
                  'cell--ghost': ghostAt(ri, ci),
                  'cell--hoverable': hasSelection && !board[ri]?.[ci] && !ghostAt(ri, ci),
                  [`cell--${premium(ri, ci)}`]: !board[ri]?.[ci] && !ghostAt(ri, ci) && premium(ri, ci) !== 'normal',
                }"
                @click="handleCellClick(ri, ci)"
              >
                <span v-if="board[ri]?.[ci]" class="tile-letter">{{ board[ri][ci]!.toUpperCase() }}</span>
                <template v-else-if="ghostAt(ri, ci)">
                  <span class="ghost-letter">{{ blankLetterAt(ri, ci) ?? '?' }}</span>
                </template>
                <span v-else-if="premium(ri, ci) !== 'normal'" class="premium-label">
                  {{ PREMIUM_LABELS[premium(ri, ci)] }}
                </span>
              </div>
            </td>
            <td class="w-6 text-center label">{{ ri + 1 }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th class="h-5 w-6" />
            <th v-for="(label, ci) in COL_LABELS" :key="ci" class="h-5 w-9 text-center label">
              {{ label }}
            </th>
            <th class="h-5 w-6" />
          </tr>
        </tfoot>
      </table>
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
      <button class="blank-picker__cancel" @click="pickerPos = null">
        Cancel
      </button>
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

.board-table {
  border-collapse: separate;
  border-spacing: 1px;
}

.label {
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}

.cell {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-cell);
  box-shadow: var(--shadow-cell-inset);
  transition: all 0.15s;
  position: relative;
  cursor: default;
}

.cell--hoverable {
  cursor: pointer;
}
.cell--hoverable:hover {
  box-shadow: var(--shadow-cell-inset), 0 0 0 1px var(--color-outline);
}

.cell--occupied {
  background: var(--color-placed-tile-bg);
  border: 1px solid var(--color-outline);
  box-shadow: var(--shadow-cell-occupied);
}

.tile-letter {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-placed-tile-letter);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
}

.cell--ghost {
  background: rgba(212, 197, 169, 0.35);
  border: 2px solid var(--color-active-turn);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
}

.ghost-letter {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-active-turn);
}

.cell--dl  { background: var(--color-premium-dl-bg);  border: 1px solid var(--color-outline-variant); }
.cell--tl  { background: var(--color-premium-tl-bg);  border: 1px solid var(--color-outline-variant); }
.cell--dw  { background: var(--color-premium-dw-bg);  border: 1px solid var(--color-outline-variant); }
.cell--tw  { background: var(--color-premium-tw-bg);  border: 1px solid var(--color-outline-variant); }
.cell--center { background: var(--color-premium-center-bg); border: 1px solid var(--color-outline-variant); }

.premium-label {
  font-family: var(--font-sans);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.cell--dl  .premium-label { color: var(--color-premium-dl-label); }
.cell--tl  .premium-label { color: var(--color-premium-tl-label); }
.cell--dw  .premium-label { color: var(--color-premium-dw-label); }
.cell--tw  .premium-label { color: var(--color-premium-tw-label); }
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
