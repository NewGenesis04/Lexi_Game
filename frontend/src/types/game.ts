export interface Position {
  row: number
  col: number
}

export interface Tile {
  letter: string
  plays_as?: string
}

export interface PlacedTile extends Position {
  letter: string
  plays_as?: string
}

export type MoveType = 'place' | 'swap' | 'pass'

export interface MovePayload {
  type: MoveType
  tiles?: PlacedTile[]
  letters?: string[]
}

export type GamePhase = 'lobby' | 'playing' | 'adjourned' | 'paused' | 'finished'

export interface PlayerState {
  id: string
  nickname: string
  rack: Tile[]
  score: number
  time_remaining: number
  connected: boolean
  is_current_player: boolean
}

export interface MoveRecord {
  type: MoveType
  player_index: number
  tiles?: PlacedTile[]
  letters?: string[]
  score?: number
  words_formed?: string[]
  timestamp: string
}

export interface GameState {
  code: string
  board: (Tile | null)[][]
  bag_remaining: number
  players: [PlayerState, PlayerState]
  current_player_index: number
  phase: GamePhase
  move_history: MoveRecord[]
  dictionary: 'TWL' | 'CSW21'
  consecutive_passes: number
  last_move: MoveRecord | null
  time_limit: number
  winner: number | null
  created_at: string
  updated_at: string
}

export interface CreateGamePayload {
  nickname: string
  time_limit: number
  dictionary: 'TWL' | 'CSW21'
}

export interface CreateGameResponse {
  code: string
  session_token: string
  game: GameState
}

export interface JoinGamePayload {
  code: string
  nickname: string
}

export interface JoinGameResponse {
  session_token: string
  game: GameState
}

export interface PlayerSession {
  token: string
  nickname: string
  player_index: number
}

export interface ApiError {
  detail: string
}

export interface ToastMessage {
  id: string
  text: string
  type: 'error' | 'info' | 'success'
}

export type PremiumType = 'normal' | 'dl' | 'tl' | 'dw' | 'tw' | 'center'

export interface SquareTheme {
  bg: string
  activeBg: string
  label: string
  labelColor: string
}

export interface BoardTheme {
  name: string
  boardBg: string
  border: string
  ghostBg: string
  ghostBorder: string
  occupiedBg: string
  squares: Record<PremiumType, SquareTheme>
}
