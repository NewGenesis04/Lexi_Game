import type {
  CreateGameRequest,
  CreateGameResponse,
  GameStateOut,
  JoinGameRequest,
  JoinGameResponse,
  MoveRequest,
} from '../types/game'

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiRequestError(0, 'Something went wrong. Please try again later.')
  }
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

export function createGame(payload: CreateGameRequest) {
  return request<CreateGameResponse>('/games', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function joinGame(code: string, payload: JoinGameRequest) {
  return request<JoinGameResponse>(`/games/${code}/join`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchGame(code: string, token: string) {
  return request<GameStateOut>(`/games/${code}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function submitMove(code: string, payload: MoveRequest, token: string) {
  return request<GameStateOut>(`/games/${code}/moves`, {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function forfeitGame(code: string, token: string) {
  return request<GameStateOut>(`/games/${code}/forfeit`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}
