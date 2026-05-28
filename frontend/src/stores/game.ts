import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Dictionary,
  GamePhase,
  GameStateOut,
  MoveRequest,
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

export const useGameStore = defineStore('game', () => {
  const game = ref<GameStateOut | null>(null)
  const session = ref<PlayerSession | null>(null)
  const connected = ref(false)
  const toasts = ref<ToastMessage[]>([])
  let sseConnection: SSEConnection | null = null

  const phase = computed<GamePhase>(() => game.value?.phase ?? 'created')

  const myPlayer = computed(() => {
    if (!game.value || !session.value) return null
    return game.value.players.find((p) => p.id === session.value!.player_id) ?? null
  })

  const opponent = computed(() => {
    if (!game.value || !session.value) return null
    return game.value.players.find((p) => p.id !== session.value!.player_id) ?? null
  })

  const isMyTurn = computed(() => {
    if (!game.value || !session.value) return false
    const current = game.value.players[game.value.current_player_index]
    return current?.id === session.value.player_id
  })

  function updateLocalState(payload: GameStateOut) {
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

  async function fetchGameState(code: string) {
    if (!session.value) throw new Error('No session')
    const g = await apiFetchGame(code, session.value.token)
    updateLocalState(g)
    return g
  }

  async function createGame(
    nickname: string,
    time_per_player_secs: number,
    dictionary: Dictionary,
  ) {
    const res = await apiCreateGame({ nickname, time_per_player_secs, dictionary })
    session.value = { token: res.token, player_id: res.player_id, nickname }
    const state = await apiFetchGame(res.code, res.token)
    updateLocalState(state)
    return res
  }

  async function joinGame(code: string, nickname: string) {
    const res = await apiJoinGame(code, { nickname })
    session.value = { token: res.token, player_id: res.player_id, nickname }
    updateLocalState(res.state)
    return res
  }

  async function submitMove(code: string, payload: MoveRequest) {
    if (!session.value) throw new Error('No session')
    const state = await apiSubmitMove(code, payload, session.value.token)
    updateLocalState(state)
  }

  async function forfeit(code: string) {
    if (!session.value) throw new Error('No session')
    const state = await apiForfeit(code, session.value.token)
    updateLocalState(state)
  }

  function connectSSEStream() {
    if (!session.value) {
      addToast('Cannot connect: no session', 'error')
      return
    }
    const url = `${import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'}/events?token=${session.value.token}`
    sseConnection = connectSSE(url, (data) => {
      updateLocalState(data as GameStateOut)
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
    myPlayer,
    opponent,
    isMyTurn,
    updateLocalState,
    addToast,
    clearToasts,
    fetchGameState,
    createGame,
    joinGame,
    submitMove,
    forfeit,
    connectSSEStream,
    disconnectSSE,
    reset,
  }
})
