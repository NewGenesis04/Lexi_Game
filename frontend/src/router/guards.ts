import type { RouteLocationNormalized } from 'vue-router'
import { useGameStore } from '../stores/game'
import { ApiRequestError } from '../services/api'

export async function gameGuard(
  to: RouteLocationNormalized,
) {
  const store = useGameStore()
  const code = to.params.code as string

  store.disconnectSSE()

  try {
    await store.fetchGame(code)
    store.connectSSEStream()
  } catch (err) {
    if (err instanceof ApiRequestError && err.status === 404) {
      store.addToast('Game not found — it may have ended or been removed.', 'error')
    } else {
      store.addToast('Failed to load game. Please try again.', 'error')
    }
    store.reset()
    return { name: 'lobby' }
  }
}
