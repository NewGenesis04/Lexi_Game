import { ref, watch } from 'vue'
import { BOARD_THEMES, getTheme } from '../constants/board'
import type { BoardTheme } from '../types/game'

const STORAGE_KEY = 'neo-scrabble-theme'

function loadSaved(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? BOARD_THEMES[0].name
  } catch {
    return BOARD_THEMES[0].name
  }
}

export function useTheme() {
  const themeName = ref(loadSaved())
  const theme = ref<BoardTheme>(getTheme(themeName.value))

  watch(themeName, (name) => {
    theme.value = getTheme(name)
    try {
      localStorage.setItem(STORAGE_KEY, name)
    } catch { /* noop */ }
  })

  function setTheme(name: string) {
    themeName.value = name
  }

  return { themeName, theme, setTheme, availableThemes: BOARD_THEMES }
}
