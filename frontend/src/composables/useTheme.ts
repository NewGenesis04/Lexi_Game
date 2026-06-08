import { ref, watchEffect } from 'vue'

const stored = localStorage.getItem('lexi-theme')
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const theme = ref<'light' | 'dark'>(
  stored === 'light' || stored === 'dark' ? stored : prefersDark ? 'dark' : 'light'
)

watchEffect(() => {
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('lexi-theme', theme.value)
})

export function useTheme() {
  const toggle = () => { theme.value = theme.value === 'dark' ? 'light' : 'dark' }
  return { theme, toggle }
}
