import { ref, computed } from 'vue'
import type { MoveRequest, PlacedTileIn, TileOut } from '../types/game'

interface GhostTile {
  rackIndex: number
  row: number
  col: number
}

export function usePendingMove() {
  const selectedRackIndex = ref<number | null>(null)
  const ghosts = ref<Map<string, GhostTile>>(new Map())
  const swapMode = ref(false)
  const swapIndices = ref<Set<number>>(new Set())
  const blankLetterMap = ref<Map<string, string>>(new Map())

  const hasPendingPlacements = computed(() => ghosts.value.size > 0)
  const hasSwapSelection = computed(() => swapIndices.value.size > 0)

  function buildPlacePayload(rack: TileOut[]): PlacedTileIn[] {
    const out: PlacedTileIn[] = []
    for (const g of ghosts.value.values()) {
      const tile = rack[g.rackIndex]
      if (!tile) continue
      const isBlank = tile.letter === ' '
      const chosen = isBlank ? (blankLetterMap.value.get(`${g.row},${g.col}`) ?? '?') : ''
      out.push({
        row: g.row,
        col: g.col,
        letter: isBlank ? ' ' : tile.letter,
        plays_as: isBlank ? chosen : null,
      })
    }
    return out
  }

  function buildSwapPayload(rack: TileOut[]): string[] {
    return [...swapIndices.value].map((i) => rack[i]?.letter ?? '')
  }

  function buildMovePayload(rack: TileOut[]): MoveRequest | null {
    if (ghosts.value.size > 0) {
      return { type: 'place', tiles: buildPlacePayload(rack) }
    }
    if (swapIndices.value.size > 0) {
      return { type: 'swap', letters: buildSwapPayload(rack) }
    }
    return null
  }

  function selectRackTile(index: number) {
    if (swapMode.value) {
      toggleSwapIndex(index)
      return
    }
    if (isPlaced(index)) {
      removeByRackIndex(index)
      return
    }
    selectedRackIndex.value = selectedRackIndex.value === index ? null : index
  }

  function tryPlaceTile(row: number, col: number, rack: TileOut[]): boolean {
    if (selectedRackIndex.value === null) return false
    const key = `${row},${col}`
    if (ghosts.value.has(key)) return false
    if (isRackIndexUsed(selectedRackIndex.value)) return false
    if (!rack[selectedRackIndex.value]) return false

    ghosts.value.set(key, {
      rackIndex: selectedRackIndex.value,
      row,
      col,
    })
    selectedRackIndex.value = null
    return true
  }

  function tryRemoveGhost(row: number, col: number): boolean {
    const key = `${row},${col}`
    if (!ghosts.value.has(key)) return false
    ghosts.value.delete(key)
    blankLetterMap.value.delete(key)
    return true
  }

  function isPlaced(rackIndex: number): boolean {
    for (const g of ghosts.value.values()) {
      if (g.rackIndex === rackIndex) return true
    }
    return false
  }

  function removeByRackIndex(rackIndex: number) {
    for (const [key, g] of ghosts.value.entries()) {
      if (g.rackIndex === rackIndex) {
        ghosts.value.delete(key)
        blankLetterMap.value.delete(key)
        selectedRackIndex.value = rackIndex
        return
      }
    }
  }

  function isRackIndexUsed(rackIndex: number): boolean {
    for (const g of ghosts.value.values()) {
      if (g.rackIndex === rackIndex) return true
    }
    return false
  }

  function ghostAt(row: number, col: number): GhostTile | undefined {
    return ghosts.value.get(`${row},${col}`)
  }

  function clearAll() {
    ghosts.value = new Map()
    blankLetterMap.value = new Map()
    selectedRackIndex.value = null
  }

  function toggleSwapMode() {
    swapMode.value = !swapMode.value
    if (!swapMode.value) swapIndices.value = new Set()
    selectedRackIndex.value = null
  }

  function toggleSwapIndex(index: number) {
    const next = new Set(swapIndices.value)
    next.has(index) ? next.delete(index) : next.add(index)
    swapIndices.value = next
  }

  function setBlankLetter(row: number, col: number, letter: string) {
    blankLetterMap.value.set(`${row},${col}`, letter)
  }

  function reset() {
    selectedRackIndex.value = null
    ghosts.value = new Map()
    swapMode.value = false
    swapIndices.value = new Set()
    blankLetterMap.value = new Map()
  }

  return {
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
    isPlaced,
    ghostAt,
    clearAll,
    toggleSwapMode,
    toggleSwapIndex,
    setBlankLetter,
    reset,
  }
}
