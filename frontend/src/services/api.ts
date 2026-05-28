import type {
  CreateGamePayload,
  CreateGameResponse,
  GameState,
  JoinGamePayload,
  JoinGameResponse,
  MovePayload,
} from '../types/game'

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiRequestError(res.status, body.detail ?? 'Unknown error')
  }
  return res.json() as Promise<T>
}

export class ApiRequestError extends Error {
  status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

export function createGame(payload: CreateGamePayload, token?: string) {
  return request<CreateGameResponse>('/games', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
}

export function joinGame(code: string, payload: JoinGamePayload) {
  return request<JoinGameResponse>(`/games/${code}/join`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function submitMove(code: string, payload: MovePayload, token: string) {
  return request<{ game: GameState }>(`/games/${code}/moves`, {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function forfeitGame(code: string, token: string) {
  return request<{ game: GameState }>(`/games/${code}/forfeit`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function fetchGame(code: string) {
  return request<GameState>(`/games/${code}`)
}
