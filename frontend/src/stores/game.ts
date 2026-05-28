import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  GameState,
  GamePhase,
  PlayerSession,
  ToastMessage,
} from '../types/game'
import {
  createGame as apiCreateGame,
  fetchGame as apiFetchGame,
  forfeitGame as apiForfeit,
  joinGame as apiJoinGame,
  submitMove as apiSubmitMove,
} from '../services/api'
import { connectSSE, type SSEConnection } from '../composables/sse'
import type { MovePayload } from '../types/game'

export const useGameStore = defineStore('game', () => {
  const game = ref<GameState | null>(null)
  const session = ref<PlayerSession | null>(null)
  const connected = ref(false)
  const toasts = ref<ToastMessage[]>([])
  let sseConnection: SSEConnection | null = null

  const phase = computed<GamePhase>(() => game.value?.phase ?? 'lobby')
  const isMyTurn = computed(() => {
    if (!game.value || !session.value) return false
    return game.value.current_player_index === session.value.player_index
  })
  const myPlayerIndex = computed(() => session.value?.player_index ?? 0)
  const myPlayer = computed(() => {
    if (!game.value) return null
    return game.value.players[session.value?.player_index ?? 0]
  })
  const opponent = computed(() => {
    if (!game.value) return null
    return game.value.players[session.value?.player_index === 0 ? 1 : 0]
  })

  function updateLocalState(payload: GameState) {
    game.value = payload
  }

  function addToast(text: string, type: ToastMessage['type'] = 'info') {
    const id = crypto.randomUUID()
    toasts.value.push({ id, text, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 5000)
  }

  function clearToasts() {
    toasts.value = []
  }

  async function fetchGame(code: string) {
    const g = await apiFetchGame(code)
    updateLocalState(g)
    return g
  }

  async function createGame(
    nickname: string,
    timeLimit: number,
    dictionary: 'TWL' | 'CSW21',
  ) {
    const res = await apiCreateGame({ nickname, time_limit: timeLimit, dictionary })
    session.value = { token: res.session_token, nickname, player_index: 0 }
    updateLocalState(res.game)
    return res
  }

  async function joinGame(code: string, nickname: string) {
    const res = await apiJoinGame(code, { code, nickname })
    session.value = { token: res.session_token, nickname, player_index: 1 }
    updateLocalState(res.game)
    return res
  }

  async function submitMove(code: string, payload: MovePayload) {
    if (!session.value) throw new Error('No session')
    const res = await apiSubmitMove(code, payload, session.value.token)
    updateLocalState(res.game)
    return res
  }

  async function forfeit(code: string) {
    if (!session.value) throw new Error('No session')
    const res = await apiForfeit(code, session.value.token)
    updateLocalState(res.game)
    return res
  }

  function connectSSEStream() {
    if (!session.value) {
      addToast('Cannot connect: no session', 'error')
      return
    }
    const url = `${import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'}/events?token=${session.value.token}`
    sseConnection = connectSSE(url, (data) => {
      updateLocalState(data as GameState)
    })
    connected.value = true
  }

  function disconnectSSE() {
    if (sseConnection) {
      sseConnection.close()
      sseConnection = null
    }
    connected.value = false
  }

  function reset() {
    disconnectSSE()
    game.value = null
    session.value = null
    toasts.value = []
  }

  return {
    game,
    session,
    connected,
    toasts,
    phase,
    isMyTurn,
    myPlayerIndex,
    myPlayer,
    opponent,
    updateLocalState,
    addToast,
    clearToasts,
    fetchGame,
    createGame,
    joinGame,
    submitMove,
    forfeit,
    connectSSEStream,
    disconnectSSE,
    reset,
  }
})
