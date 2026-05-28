<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Tile } from '../../types/game'
import { PREMIUM_LAYOUT, getTheme } from '../../constants/board'

const props = defineProps<{
  board: (Tile | null)[][]
  ghostAt: (row: number, col: number) => { rackIndex: number; row: number; col: number } | undefined
  blankLetterAt: (row: number, col: number) => string | undefined
  hasSelection: boolean
  themeName?: string
}>()

const emit = defineEmits<{
  placeTile: [row: number, col: number]
  removeGhost: [row: number, col: number]
  setBlankLetter: [row: number, col: number, letter: string]
}>()

const theme = computed(() => getTheme(props.themeName ?? 'Dark'))
const pickerPos = ref<{ row: number; col: number } | null>(null)

const COL_LABELS = 'ABCDEFGHIJKLMNO'.split('')

function handleCellClick(row: number, col: number) {
  const ghost = props.ghostAt(row, col)
  if (ghost) {
    const tile = props.board[row]?.[col]
    if (tile?.letter === ' ') {
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

function cellClasses(row: number, col: number) {
  const premium = PREMIUM_LAYOUT[row][col]
  const sq = theme.value.squares[premium]
  const isGhost = props.ghostAt(row, col)

  if (isGhost) {
    return `${theme.value.ghostBg} ${theme.value.ghostBorder} border text-white text-xs font-bold flex items-center justify-center`
  }
  if (props.board[row]?.[col]) {
    return `${theme.value.occupiedBg} ${theme.value.border} border text-neutral-900 text-xs font-bold flex items-center justify-center hover:brightness-110`
  }
  const hover = props.hasSelection ? 'hover:brightness-125 cursor-pointer' : ''
  return `${sq.bg} ${theme.value.border} border ${hover} flex items-center justify-center`
}

function cellContent(row: number, col: number) {
  const ghost = props.ghostAt(row, col)
  if (ghost) {
    const blankLetter = props.blankLetterAt(row, col)
    return blankLetter ?? '?'
  }
  const placed = props.board[row]?.[col]
  if (placed) return placed.letter

  const premium = PREMIUM_LAYOUT[row][col]
  const sq = theme.value.squares[premium]
  return sq.label
}

function cellLabelClasses(row: number, col: number) {
  if (props.board[row]?.[col] || props.ghostAt(row, col)) return 'text-xs font-bold'
  const premium = PREMIUM_LAYOUT[row][col]
  return `text-[10px] font-semibold ${theme.value.squares[premium].labelColor}`
}

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

function pickLetter(letter: string) {
  if (!pickerPos.value) return
  emit('setBlankLetter', pickerPos.value.row, pickerPos.value.col, letter)
  pickerPos.value = null
}
</script>

<template>
  <div class="relative">
    <div
      class="inline-block rounded-lg border-2 p-1 shadow-lg"
      :class="[theme.boardBg, theme.border]"
    >
      <table class="border-collapse">
        <thead>
          <tr>
            <th class="h-5 w-6" />
            <th
              v-for="(label, ci) in COL_LABELS"
              :key="ci"
              class="h-5 w-9 text-[10px] font-semibold"
              :class="theme.squares.normal.labelColor"
            >
              {{ label }}
            </th>
            <th class="h-5 w-6" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, ri) in board"
            :key="ri"
          >
            <td class="w-6 text-center text-[10px] font-semibold" :class="theme.squares.normal.labelColor">
              {{ ri + 1 }}
            </td>
            <td
              v-for="(_, ci) in row"
              :key="ci"
              class="h-9 w-9"
              :class="cellClasses(ri, ci)"
              @click="handleCellClick(ri, ci)"
            >
              <span :class="cellLabelClasses(ri, ci)">
                {{ cellContent(ri, ci) }}
              </span>
            </td>
            <td class="w-6 text-center text-[10px] font-semibold" :class="theme.squares.normal.labelColor">
              {{ ri + 1 }}
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th class="h-5 w-6" />
            <th
              v-for="(label, ci) in COL_LABELS"
              :key="ci"
              class="h-5 w-9 text-[10px] font-semibold"
              :class="theme.squares.normal.labelColor"
            >
              {{ label }}
            </th>
            <th class="h-5 w-6" />
          </tr>
        </tfoot>
      </table>
    </div>

    <div
      v-if="!board.length"
      class="absolute inset-0 flex items-center justify-center text-neutral-500"
    >
      Loading board…
    </div>

    <div
      v-if="pickerPos"
      class="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-lg border border-neutral-500 bg-neutral-900 p-3 shadow-xl"
    >
      <div class="mb-2 text-center text-xs text-neutral-400">
        Choose letter for blank
      </div>
      <div class="grid grid-cols-7 gap-1">
        <button
          v-for="letter in LETTERS"
          :key="letter"
          class="flex h-7 w-7 items-center justify-center rounded bg-neutral-700 text-xs font-bold text-white hover:bg-blue-600"
          @click="pickLetter(letter)"
        >
          {{ letter }}
        </button>
      </div>
      <button
        class="mt-2 w-full rounded bg-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:text-white"
        @click="pickerPos = null"
      >
        Cancel
      </button>
    </div>
  </div>
</template>
