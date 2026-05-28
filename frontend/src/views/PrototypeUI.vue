<script setup lang="ts">
import { ref } from 'vue'

const COL_LABELS = 'ABCDEFGHIJKLMNO'.split('')

type Screen = 'lobby' | 'game' | 'finished'
const screen = ref<Screen>('game')

const tab = ref<'create' | 'join'>('create')

// ─── Artisan Tabletop System ───────────────────────────────────────

const colors = {
  surface: '#131313',
  'surface-dim': '#131313',
  'surface-bright': '#393939',
  'surface-container-lowest': '#0e0e0e',
  'surface-container-low': '#1b1c1c',
  surfaceContainer: '#202020',
  'surface-container-high': '#2a2a2a',
  'surface-container-highest': '#353535',
  onSurface: '#e5e2e1',
  'on-surface-variant': '#d3c3c0',
  outline: '#9c8d8b',
  'outline-variant': '#504442',
  primary: '#e3beb8',
  'on-primary': '#422a26',
  'primary-container': '#3e2723',
  secondary: '#d6c3bc',
  tertiary: '#ffb5a0',
  'tertiary-container': '#5a1200',
  'primary-fixed-dim': '#e3beb8',
}

// Premium square styling per type: { bg, label, labelColor }
function cellStyle(type: number) {
  switch (type) {
    case 1: // DL
      return { background: colors.surfaceContainer, color: colors.secondary }
    case 4: // TL
      return { background: colors['surface-container-high'], color: colors['on-surface-variant'] }
    case 2: // DW
      return { background: colors['primary-container'], color: colors['primary-fixed-dim'] }
    case 3: // TW
      return { background: colors['tertiary-container'], color: colors.tertiary }
    case 5: // center ★
      return { background: colors['primary-container'], color: colors.primary }
    default:
      return { background: colors.surface, color: 'transparent' }
  }
}

const PREMIUM_LABELS: Record<number, string> = {
  1: 'DL', 4: 'TL', 2: 'DW', 3: 'TW', 5: '★'
}

const PREMIUM = [
  [3,0,0,1,0,0,0,3,0,0,0,1,0,0,3],
  [0,2,0,0,0,4,0,0,0,4,0,0,0,2,0],
  [0,0,2,0,0,0,4,0,4,0,0,0,2,0,0],
  [1,0,0,2,0,0,0,1,0,0,0,2,0,0,1],
  [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
  [0,4,0,0,0,4,0,0,0,4,0,0,0,4,0],
  [0,0,4,0,0,0,4,0,4,0,0,0,4,0,0],
  [3,0,0,1,0,0,0,5,0,0,0,1,0,0,3],
  [0,0,4,0,0,0,4,0,4,0,0,0,4,0,0],
  [0,4,0,0,0,4,0,0,0,4,0,0,0,4,0],
  [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
  [1,0,0,2,0,0,0,1,0,0,0,2,0,0,1],
  [0,0,2,0,0,0,4,0,4,0,0,0,2,0,0],
  [0,2,0,0,0,4,0,0,0,4,0,0,0,2,0],
  [3,0,0,1,0,0,0,3,0,0,0,1,0,0,3],
]

interface PlacedTile {
  letter: string
  points: number
  row: number
  col: number
}

const placedTiles: PlacedTile[] = [
  { letter: 'S', points: 1, row: 7, col: 5 },
  { letter: 'T', points: 1, row: 7, col: 6 },
  { letter: 'A', points: 1, row: 7, col: 7 },
  { letter: 'R', points: 1, row: 7, col: 8 },
  { letter: 'E', points: 1, row: 7, col: 9 },
  { letter: 'Q', points: 10, row: 4, col: 7 },
  { letter: 'U', points: 1, row: 5, col: 7 },
  { letter: 'I', points: 1, row: 6, col: 7 },
  { letter: 'T', points: 1, row: 8, col: 7 },
  { letter: 'E', points: 1, row: 9, col: 7 },
]

const rackTiles = [
  { letter: 'A', points: 1 },
  { letter: 'B', points: 3 },
  { letter: 'E', points: 1 },
  { letter: 'G', points: 2 },
  { letter: 'L', points: 1 },
  { letter: 'O', points: 1 },
  { letter: 'Z', points: 10 },
]

const selectedIndex = ref<number | null>(null)
const hoveredIndex = ref<number | null>(null)

function tileAt(row: number, col: number) {
  return placedTiles.find(t => t.row === row && t.col === col)
}

function premiumType(row: number, col: number) {
  return PREMIUM[row][col]
}

function isPlaced(row: number, col: number) {
  return !!tileAt(row, col)
}
</script>

<template>
  <div class="min-h-screen" :style="{ background: colors.surface, color: colors.onSurface, fontFamily: 'EB Garamond, serif' }">

    <!-- View Switcher -->
    <div class="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex gap-2" :style="{ fontFamily: 'Work Sans, sans-serif' }">
      <button
        :style="{
          background: screen === 'lobby' ? colors.primary : colors['surface-container-low'],
          color: screen === 'lobby' ? colors['on-primary'] : colors['on-surface-variant'],
          border: `1px solid ${colors.outline}`,
        }"
        class="rounded px-4 py-2 text-xs font-bold tracking-[0.1em] uppercase transition-all duration-200 hover:opacity-80"
        @click="screen = 'lobby'"
      >Lobby</button>
      <button
        :style="{
          background: screen === 'game' ? colors.primary : colors['surface-container-low'],
          color: screen === 'game' ? colors['on-primary'] : colors['on-surface-variant'],
          border: `1px solid ${colors.outline}`,
        }"
        class="rounded px-4 py-2 text-xs font-bold tracking-[0.1em] uppercase transition-all duration-200 hover:opacity-80"
        @click="screen = 'game'"
      >Game</button>
      <button
        :style="{
          background: screen === 'finished' ? colors.primary : colors['surface-container-low'],
          color: screen === 'finished' ? colors['on-primary'] : colors['on-surface-variant'],
          border: `1px solid ${colors.outline}`,
        }"
        class="rounded px-4 py-2 text-xs font-bold tracking-[0.1em] uppercase transition-all duration-200 hover:opacity-80"
        @click="screen = 'finished'"
      >Game Over</button>
    </div>

    <!-- ==================== LOBBY ==================== -->
    <div v-if="screen === 'lobby'" class="flex min-h-screen items-center justify-center p-5">
      <div
        class="w-full max-w-md p-8"
        :style="{
          background: colors['primary-container'],
          borderRadius: '0.5rem',
          border: `1px solid ${colors.outline}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
        }"
      >
        <h1
          class="text-center mb-6"
          :style="{ fontFamily: 'EB Garamond, serif', fontSize: '32px', fontWeight: 500, lineHeight: '1.2', color: colors.primary }"
        >
          NEO SCRABBLE
        </h1>

        <div class="flex rounded-sm mb-6" :style="{ background: colors['surface-container-lowest'], padding: '2px' }">
          <button
            :style="{
              background: tab === 'create' ? colors.outline : 'transparent',
              color: tab === 'create' ? colors['surface-container-lowest'] : colors['on-surface-variant'],
            }"
            class="flex-1 rounded px-4 py-2 text-xs font-bold tracking-[0.1em] uppercase transition-all"
            :class="{ 'hover:opacity-80': true }"
            @click="tab = 'create'"
          >Create</button>
          <button
            :style="{
              background: tab === 'join' ? colors.outline : 'transparent',
              color: tab === 'join' ? colors['surface-container-lowest'] : colors['on-surface-variant'],
            }"
            class="flex-1 rounded px-4 py-2 text-xs font-bold tracking-[0.1em] uppercase transition-all"
            :class="{ 'hover:opacity-80': true }"
            @click="tab = 'join'"
          >Join</button>
        </div>

        <form v-if="tab === 'create'" class="space-y-4">
          <input
            placeholder="Your nickname"
            :style="{
              background: colors['surface-container-lowest'],
              color: colors.onSurface,
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'EB Garamond, serif',
              fontSize: '18px',
              outline: 'none',
            }"
          />
          <select
            :style="{
              background: colors['surface-container-lowest'],
              color: colors.onSurface,
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.1em',
              outline: 'none',
            }"
          >
            <option>North American (TWL)</option>
            <option>International (CSW21)</option>
          </select>
          <select
            :style="{
              background: colors['surface-container-lowest'],
              color: colors.onSurface,
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.1em',
              outline: 'none',
            }"
          >
            <option>1 min per player</option>
            <option>3 min per player</option>
            <option>5 min per player</option>
            <option>10 min per player</option>
          </select>
          <button
            :style="{
              background: `linear-gradient(180deg, ${colors.outline}, #8a7d7b)`,
              color: colors['surface-container-lowest'],
              border: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: 'pointer',
            }"
          >Create Game</button>
        </form>

        <form v-else class="space-y-4">
          <input
            placeholder="6-digit game code"
            maxlength="6"
            :style="{
              background: colors['surface-container-lowest'],
              color: colors.onSurface,
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              textAlign: 'center',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '18px',
              fontWeight: 600,
              letterSpacing: '0.3em',
              outline: 'none',
            }"
          />
          <input
            placeholder="Your nickname"
            :style="{
              background: colors['surface-container-lowest'],
              color: colors.onSurface,
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'EB Garamond, serif',
              fontSize: '18px',
              outline: 'none',
            }"
          />
          <button
            :style="{
              background: `linear-gradient(180deg, ${colors.outline}, #8a7d7b)`,
              color: colors['surface-container-lowest'],
              border: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
              borderRadius: '0.25rem',
              padding: '12px 16px',
              width: '100%',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: 'pointer',
            }"
          >Join Game</button>
        </form>
      </div>
    </div>

    <!-- ==================== GAME ==================== -->
    <div v-if="screen === 'game' || screen === 'finished'" class="min-h-screen flex flex-col">
      <!-- Header -->
      <header
        :style="{
          background: colors['surface-container-low'],
          borderBottom: `1px solid ${colors['outline-variant']}`,
        }"
        class="flex items-center justify-between px-6 py-3"
      >
        <span :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">GAME · XY7K9M</span>
        <div class="flex items-center gap-3">
          <button
            :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors.secondary, border: `1px solid ${colors.outline}`, borderRadius: '0.25rem', padding: '6px 12px', background: 'transparent', cursor: 'pointer', transition: 'all 0.2s' }"
            @mouseenter="(e: any) => { e.target.style.background = colors['surface-container-high'] }"
            @mouseleave="(e: any) => { e.target.style.background = 'transparent' }"
          >Theme</button>
          <button
            :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['surface-container-lowest'], background: colors['tertiary-container'], border: 'none', borderRadius: '0.25rem', padding: '6px 12px', cursor: 'pointer', boxShadow: '0 2px 4px rgba(0,0,0,0.3)', transition: 'all 0.2s' }"
            @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
            @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
          >Leave</button>
        </div>
      </header>

      <!-- Main Content -->
      <div class="flex-1 flex flex-col lg:flex-row items-center lg:items-start justify-center gap-6 p-6" :style="{ background: colors.surface }">

        <!-- Board + Rack + Controls -->
        <div class="flex flex-col items-center gap-4">
          <!-- Board - The Artisan Tabletop -->
          <div
            :style="{
              background: `linear-gradient(180deg, ${colors['surface-dim']}, ${colors['surface-container-low']})`,
              borderRadius: '0.625rem',
              border: `2px solid ${colors.outline}`,
              boxShadow: '0 6px 24px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
              padding: '8px',
            }"
          >
            <table class="border-collapse">
              <thead>
                <tr>
                  <th class="h-5 w-6" />
                  <th v-for="(label, ci) in COL_LABELS" :key="ci" class="h-5 w-9 text-center" :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">
                    {{ label }}
                  </th>
                  <th class="h-5 w-6" />
                </tr>
              </thead>
              <tbody>
                <tr v-for="(_, ri) in 15" :key="ri">
                  <td class="w-6 text-center" :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">{{ ri + 1 }}</td>
                  <td v-for="(_, ci) in 15" :key="ci" class="h-9 w-9 p-[1px]">
                    <div
                      :style="{
                        width: '100%',
                        height: '100%',
                        boxSizing: 'border-box',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isPlaced(ri, ci) ? '#d4c5a9' : cellStyle(premiumType(ri, ci)).background,
                        borderRadius: '0.125rem',
                        position: 'relative',
                        border: `1px solid ${isPlaced(ri, ci) ? colors.outline : colors['outline-variant']}`,
                        boxShadow: isPlaced(ri, ci)
                          ? '0 2px 6px rgba(0,0,0,0.5)'
                          : 'inset 0 1px 2px rgba(0,0,0,0.3)',
                        transition: 'all 0.15s',
                      }"
                    >
                      <!-- Placed tile -->
                      <span v-if="isPlaced(ri, ci)" :style="{ fontFamily: 'EB Garamond, serif', fontSize: '18px', fontWeight: 600, color: '#1a1a1a', textShadow: '0 1px 0 rgba(255,255,255,0.3)' }">
                        {{ tileAt(ri, ci)?.letter }}
                        <span :style="{ position: 'absolute', bottom: '1px', right: '2px', fontFamily: 'Work Sans, sans-serif', fontSize: '8px', fontWeight: 600, color: '#5a4a3a' }">{{ tileAt(ri, ci)?.points }}</span>
                      </span>
                      <!-- Premium label -->
                      <span v-else-if="premiumType(ri, ci) !== 0" :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '8px', fontWeight: 700, letterSpacing: '0.1em', color: cellStyle(premiumType(ri, ci)).color }">
                        {{ PREMIUM_LABELS[premiumType(ri, ci)] }}
                      </span>
                    </div>
                  </td>
                  <td class="w-6 text-center" :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">{{ ri + 1 }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <th class="h-5 w-6" />
                  <th v-for="(label, ci) in COL_LABELS" :key="ci" class="h-5 w-9 text-center" :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">
                    {{ label }}
                  </th>
                  <th class="h-5 w-6" />
                </tr>
              </tfoot>
            </table>
          </div>

          <!-- Tile Rack -->
          <div
            :style="{
              background: `linear-gradient(180deg, ${colors['surface-container-low']}, ${colors.surfaceContainer})`,
              borderRadius: '0.375rem',
              border: `1px solid ${colors['outline-variant']}`,
              boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)',
              padding: '6px',
            }"
          >
            <div class="flex gap-1.5">
              <div
                v-for="(tile, i) in rackTiles"
                :key="i"
                @click="selectedIndex = selectedIndex === i ? null : i"
                @mouseenter="hoveredIndex = i"
                @mouseleave="hoveredIndex = null"
                :style="{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '44px',
                  height: '44px',
                  background: selectedIndex === i
                    ? `linear-gradient(180deg, ${colors.primary}, ${colors['primary-fixed-dim']})`
                    : hoveredIndex === i
                      ? `linear-gradient(180deg, ${colors['surface-container-highest']}, ${colors['surface-container-high']})`
                      : `linear-gradient(180deg, ${colors['surface-container-high']}, ${colors.surfaceContainer})`,
                  borderRadius: '0.25rem',
                  boxShadow: selectedIndex === i
                    ? `0 2px 8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.15), 0 0 0 1px ${colors.primary}`
                    : hoveredIndex === i
                      ? '0 4px 12px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.12)'
                      : '0 1px 3px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)',
                  cursor: 'pointer',
                  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
                  transform: selectedIndex === i
                    ? 'translateY(-6px)'
                    : hoveredIndex === i
                      ? 'translateY(-3px) scale(1.06)'
                      : 'none',
                  border: selectedIndex === i ? `1px solid ${colors.primary}` : `1px solid ${colors['outline-variant']}`,
                }"
              >
                <span :style="{ fontFamily: 'EB Garamond, serif', fontSize: '20px', fontWeight: 600, color: selectedIndex === i ? colors['on-primary'] : colors['on-surface-variant'], lineHeight: '1', textShadow: selectedIndex === i ? 'none' : '0 1px 2px rgba(0,0,0,0.5)' }">{{ tile.letter }}</span>
                <span :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '8px', fontWeight: 600, color: selectedIndex === i ? colors['on-primary'] : colors.outline, lineHeight: '1' }">{{ tile.points }}</span>
              </div>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex items-center justify-center gap-2">
            <button
              :style="{
                background: `linear-gradient(180deg, ${colors.outline}, #8a7d7b)`,
                color: colors['surface-container-lowest'],
                border: 'none',
                boxShadow: '0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
                borderRadius: '0.25rem',
                padding: '8px 20px',
                fontFamily: 'Work Sans, sans-serif',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }"
              @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
              @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
            >Submit</button>
            <button
              :style="{
                background: 'transparent',
                color: colors['on-surface-variant'],
                border: `1px solid ${colors['outline-variant']}`,
                borderRadius: '0.25rem',
                padding: '8px 16px',
                fontFamily: 'Work Sans, sans-serif',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }"
              @mouseenter="(e: any) => { e.target.style.background = colors['surface-container-high'] }"
              @mouseleave="(e: any) => { e.target.style.background = 'transparent' }"
            >Clear</button>
            <button
              :style="{
                background: 'transparent',
                color: colors['on-surface-variant'],
                border: `1px solid ${colors['outline-variant']}`,
                borderRadius: '0.25rem',
                padding: '8px 16px',
                fontFamily: 'Work Sans, sans-serif',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }"
              @mouseenter="(e: any) => { e.target.style.background = colors['surface-container-high'] }"
              @mouseleave="(e: any) => { e.target.style.background = 'transparent' }"
            >Swap</button>
            <button
              :style="{
                background: 'transparent',
                color: colors['on-surface-variant'],
                border: `1px solid ${colors['outline-variant']}`,
                borderRadius: '0.25rem',
                padding: '8px 16px',
                fontFamily: 'Work Sans, sans-serif',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }"
              @mouseenter="(e: any) => { e.target.style.background = colors['surface-container-high'] }"
              @mouseleave="(e: any) => { e.target.style.background = 'transparent' }"
            >Pass</button>
            <button
              :style="{
                background: colors['tertiary-container'],
                color: colors.tertiary,
                border: `1px solid ${colors.tertiary}`,
                borderRadius: '0.25rem',
                padding: '8px 16px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                fontFamily: 'Work Sans, sans-serif',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }"
              @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
              @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
            >Forfeit</button>
          </div>
        </div>
      </div>

      <!-- Notification Bar -->
      <div
        :style="{
          background: colors['surface-container-low'],
          borderTop: `1px solid ${colors['outline-variant']}`,
          boxShadow: '0 -2px 8px rgba(0,0,0,0.3)',
        }"
        class="fixed bottom-0 left-0 right-0 h-14 z-40 flex items-center px-6"
      >
        <div class="flex items-center gap-3">
          <span :style="{ width: '6px', height: '6px', background: colors.primary, borderRadius: '50%', display: 'inline-block' }"></span>
          <span :style="{ fontFamily: 'EB Garamond, serif', fontSize: '18px', color: colors['on-surface-variant'] }">You played <strong :style="{ color: colors.onSurface }">STARE</strong> for <strong :style="{ color: colors.primary }">24</strong> points</span>
        </div>
      </div>

      <!-- ==================== GAME OVER OVERLAY ==================== -->
      <div v-if="screen === 'finished'" class="fixed inset-0 z-50 flex items-center justify-center animate-[fadeIn_0.4s_ease-out]"
        :style="{ background: 'rgba(19,19,19,0.9)' }">
        <div
          :style="{
            background: colors['surface-container-low'],
            borderRadius: '0.5rem',
            border: `1px solid ${colors.outline}`,
            boxShadow: '0 4px 24px rgba(0,0,0,0.6)',
            padding: '32px',
            maxWidth: '360px',
            width: '100%',
            textAlign: 'center',
          }"
          class="space-y-6"
        >
          <h2 :style="{ fontFamily: 'EB Garamond, serif', fontSize: '32px', fontWeight: 600, color: colors['on-surface-variant'], letterSpacing: '-0.02em' }">
            GAME OVER
          </h2>

          <div class="space-y-1">
            <div :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">Winner</div>
            <div :style="{ fontFamily: 'EB Garamond, serif', fontSize: '28px', fontWeight: 500, color: colors.primary }">Neo</div>
            <div :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '36px', fontWeight: 600, color: colors.onSurface }">137</div>
          </div>

          <div class="space-y-2">
            <div :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '12px', fontWeight: 700, letterSpacing: '0.1em', color: colors['on-surface-variant'] }">Final Scores</div>
            <div class="space-y-2">
              <div :style="{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: colors.surfaceContainer,
                borderRadius: '0.375rem',
                border: `1px solid ${colors['outline-variant']}`,
                padding: '12px 16px',
              }">
                <span :style="{ fontFamily: 'EB Garamond, serif', fontSize: '18px', color: colors.onSurface }">Neo</span>
                <span :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '24px', fontWeight: 600, color: colors.primary }">137</span>
              </div>
              <div :style="{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: colors.surfaceContainer,
                borderRadius: '0.375rem',
                border: `1px solid ${colors['outline-variant']}`,
                padding: '12px 16px',
              }">
                <span :style="{ fontFamily: 'EB Garamond, serif', fontSize: '18px', color: colors.onSurface }">Jax</span>
                <span :style="{ fontFamily: 'Work Sans, sans-serif', fontSize: '24px', fontWeight: 600, color: colors.tertiary }">112</span>
              </div>
            </div>
          </div>

          <button
            :style="{
              background: `linear-gradient(180deg, ${colors.outline}, #8a7d7b)`,
              color: colors['surface-container-lowest'],
              border: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
              borderRadius: '0.25rem',
              padding: '12px 24px',
              width: '100%',
              fontFamily: 'Work Sans, sans-serif',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }"
          >Play Again</button>
        </div>
      </div>

    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Work+Sans:wght@400;600;700&display=swap');

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
