/* ── Rack tile (TileOut) ─────────────────── */
export interface TileOut {
  letter: string
  points: number
}

/* ── Placed tile (PlacedTileIn / PlacedTileOut) ─ */
export interface PlacedTileIn {
  row: number
  col: number
  letter: string
  plays_as?: string | null
}

export interface PlacedTileOut {
  row: number
  col: number
  letter: string
}

/* ── Move types ──────────────────────────── */
export type MoveType = 'place' | 'swap' | 'pass' | 'forfeit' | 'timeout'

export interface MoveOut {
  type: MoveType
  player_id: string
  tiles: PlacedTileOut[]
  letters: string[]
  score_delta: number
  words: string[]
}

/* ── Player (PlayerOut) ──────────────────── */
export interface PlayerOut {
  id: string
  nickname: string
  score: number
  time_remaining_secs: number
  overtime_count: number
  connected: boolean
  rack: TileOut[]  // empty list for opponent
  avatar?: string
}

/* ── Game state (GameStateOut) ────────────── */
export type GamePhase = 'created' | 'playing' | 'paused' | 'finished'
export type Dictionary = 'TWL06' | 'CSW21'

export interface GameStateOut {
  code: string
  phase: GamePhase
  dictionary: Dictionary
  board: (string | null)[][]
  bag_size: number
  players: PlayerOut[]
  current_player_index: number
  consecutive_passes: number
  last_move: MoveOut | null
  move_history: MoveOut[]
}

/* ── API request / response bodies ────────── */
export interface CreateGameRequest {
  nickname: string
  dictionary: Dictionary
  time_per_player_secs: number
  avatar?: string
}

export interface CreateGameResponse {
  code: string
  token: string
  player_id: string
}

export interface JoinGameRequest {
  nickname: string
  avatar?: string
}

export interface JoinGameResponse {
  token: string
  player_id: string
  state: GameStateOut
}

export interface PlaceMoveRequest {
  type: 'place'
  tiles: PlacedTileIn[]
}

export interface SwapMoveRequest {
  type: 'swap'
  letters: string[]
}

export interface PassMoveRequest {
  type: 'pass'
}

export type MoveRequest = PlaceMoveRequest | SwapMoveRequest | PassMoveRequest

/* ── Session (internal) ───────────────────── */
export interface PlayerSession {
  token: string
  player_id: string
  nickname: string
  avatar?: string
}

/* ── UI types ──────────────────────────────── */
export interface ToastMessage {
  id: string
  text: string
  type: 'error' | 'info' | 'success' | 'warning'
}

export type PremiumType = 'normal' | 'dl' | 'tl' | 'dw' | 'tw' | 'center'

export interface ApiError {
  detail: string
}
