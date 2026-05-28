import type { PremiumType, BoardTheme } from '../types/game'

type PremiumGrid = PremiumType[][]

function buildGrid(): PremiumGrid {
  const grid: PremiumGrid = Array.from({ length: 15 }, () =>
    Array(15).fill('normal') as PremiumType[],
  )

  const set = (cells: [number, number][], type: PremiumType) => {
    for (const [r, c] of cells) grid[r][c] = type
  }

  set([[0,0],[0,7],[0,14],[7,0],[7,14],[14,0],[14,7],[14,14]], 'tw')
  set([[1,1],[2,2],[3,3],[4,4],[1,13],[2,12],[3,11],[4,10],[10,4],[11,3],[12,2],[13,1],[10,10],[11,11],[12,12],[13,13]], 'dw')
  set([[1,5],[1,9],[5,1],[5,5],[5,9],[5,13],[9,1],[9,5],[9,9],[9,13],[13,5],[13,9]], 'tl')
  set([[0,3],[0,11],[2,6],[2,8],[3,0],[3,7],[3,14],[6,2],[6,6],[6,8],[6,12],[7,3],[7,11],[8,2],[8,6],[8,8],[8,12],[11,0],[11,7],[11,14],[12,6],[12,8],[14,3],[14,11]], 'dl')
  set([[7,7]], 'center')

  return grid
}

export const PREMIUM_LAYOUT = buildGrid()

export const BOARD_THEMES: BoardTheme[] = [
  {
    name: 'Classic',
    boardBg: 'bg-amber-50',
    border: 'border-amber-300',
    ghostBg: 'bg-green-200',
    ghostBorder: 'border-green-500',
    occupiedBg: 'bg-amber-100',
    squares: {
      normal:  { bg: 'bg-amber-50',        activeBg: 'bg-amber-200', label: '',         labelColor: 'text-transparent' },
      dl:      { bg: 'bg-blue-200',        activeBg: 'bg-blue-300',  label: 'DL',       labelColor: 'text-blue-800' },
      tl:      { bg: 'bg-blue-600',        activeBg: 'bg-blue-700',  label: 'TL',       labelColor: 'text-blue-100' },
      dw:      { bg: 'bg-pink-300',        activeBg: 'bg-pink-400',  label: 'DW',       labelColor: 'text-pink-800' },
      tw:      { bg: 'bg-red-500',         activeBg: 'bg-red-600',   label: 'TW',       labelColor: 'text-red-100' },
      center:  { bg: 'bg-pink-300',        activeBg: 'bg-pink-400',  label: '★',        labelColor: 'text-pink-800' },
    },
  },
  {
    name: 'Dark',
    boardBg: 'bg-neutral-800',
    border: 'border-neutral-600',
    ghostBg: 'bg-green-700',
    ghostBorder: 'border-green-400',
    occupiedBg: 'bg-neutral-700',
    squares: {
      normal:  { bg: 'bg-neutral-800',     activeBg: 'bg-neutral-700', label: '',         labelColor: 'text-transparent' },
      dl:      { bg: 'bg-blue-900',        activeBg: 'bg-blue-800',   label: 'DL',       labelColor: 'text-blue-300' },
      tl:      { bg: 'bg-blue-950',        activeBg: 'bg-blue-900',   label: 'TL',       labelColor: 'text-blue-400' },
      dw:      { bg: 'bg-rose-900',        activeBg: 'bg-rose-800',   label: 'DW',       labelColor: 'text-rose-300' },
      tw:      { bg: 'bg-red-950',         activeBg: 'bg-red-900',    label: 'TW',       labelColor: 'text-red-400' },
      center:  { bg: 'bg-rose-900',        activeBg: 'bg-rose-800',   label: '★',        labelColor: 'text-rose-300' },
    },
  },
  {
    name: 'High Contrast',
    boardBg: 'bg-white',
    border: 'border-gray-800',
    ghostBg: 'bg-green-300',
    ghostBorder: 'border-green-700',
    occupiedBg: 'bg-gray-100',
    squares: {
      normal:  { bg: 'bg-white',           activeBg: 'bg-gray-200',   label: '',         labelColor: 'text-transparent' },
      dl:      { bg: 'bg-sky-200',         activeBg: 'bg-sky-300',    label: 'DL',       labelColor: 'text-sky-900' },
      tl:      { bg: 'bg-sky-600',         activeBg: 'bg-sky-700',    label: 'TL',       labelColor: 'text-white' },
      dw:      { bg: 'bg-pink-200',        activeBg: 'bg-pink-300',   label: 'DW',       labelColor: 'text-pink-900' },
      tw:      { bg: 'bg-red-600',         activeBg: 'bg-red-700',    label: 'TW',       labelColor: 'text-white' },
      center:  { bg: 'bg-pink-200',        activeBg: 'bg-pink-300',   label: '★',        labelColor: 'text-pink-900' },
    },
  },
]

export function getTheme(name: string): BoardTheme {
  return BOARD_THEMES.find((t) => t.name === name) ?? BOARD_THEMES[0]
}
