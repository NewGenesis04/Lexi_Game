import type { PremiumType } from '../types/game'

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

/* ── Premium square display labels ────────────
   Multi-theme selection is frozen. These labels
   are the permanent Artisan Tabletop defaults.
   Visual styling (colours, shadows) lives in
   CSS custom properties via @theme in style.css.
   ─────────────────────────────────────────── */

export const PREMIUM_LABELS: Record<PremiumType, string> = {
  normal: '',
  dl: 'DL',
  tl: 'TL',
  dw: 'DW',
  tw: 'TW',
  center: '★',
}
