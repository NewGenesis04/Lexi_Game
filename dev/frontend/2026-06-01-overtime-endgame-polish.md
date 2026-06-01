## 2026-06-01 — Overtime system hardened; distinct end-game cards; timer display race fixed

### What was built

This session addressed four separate failure modes that all appeared once the overtime clock system was in use end-to-end: a stale-state flash on navigation, an opaque error message on word rejection, two defects in the overtime path itself (a race condition and a missing notification), and a timer display bug that zeroed the wrong player's clock.

---

**Play Again state flash — `GameView.vue:131-136`**

The "Play Again" button was wired directly to `router.push('/')`. The Pinia store retained `game.value.phase === 'finished'` across the navigation, so when the new lobby route briefly re-rendered the game overlay before unmounting, the game-over card would flash on screen and occasionally required two clicks to dismiss.

A `handlePlayAgain()` function was added at `GameView.vue:131-136` that calls `reset()` (pending-move composable), `store.disconnectSSE()`, and `store.reset()` in sequence before pushing the route. `store.reset()` at `stores/game.ts:143-149` sets `game.value = null`, which collapses the `v-if="store.phase === 'finished'"` guard at `GameView.vue:235` before the component unmounts.

---

**Error toast showing class name instead of message — `GameView.vue:87-115`**

When the backend returned a 422 for an invalid word, the `ApiRequestError` class in `services/api.ts` was thrown. Each `catch` block in `handleSubmit`, `handlePass`, and `handleForfeit` called `String(err)` on the exception, which invokes `Error.prototype.toString()` and produces `"ApiRequestError: <message>"` — the class name prepended by JavaScript's default serialisation.

All three catch blocks were updated to the guard `err instanceof Error ? err.message : String(err)` (`GameView.vue:95`, `105`, `113`). This extracts only the `.message` field from the thrown instance, which is set by `ApiRequestError` to the backend's `detail` string from the 422 response body.

---

**Overtime race condition — `game_service.py:281-305`**

The background timer (`_time_bank_task`, `game_service.py:315-344`) was implemented as an `asyncio.Task` that slept for the player's remaining time, then acquired the per-game lock to apply an overtime penalty. A race existed: if the player submitted a move at exactly 0 seconds, `_start_timer` at `game_service.py:307-313` called `game_manager.set_timer`, which cancelled the sleeping task before it could acquire the lock. The move handler's lock scope then proceeded without any time deduction or overtime check. A player who spent their entire bank on a final move would receive no penalty and would not be eliminated.

The fix moves overtime detection from the background task into the synchronous move path. `_deduct_time` at `game_service.py:281-305` was refactored to return a `bool`:

- `time_remaining_secs > 0` after deduction: stores the updated value, returns `False`.
- First overspend (`overtime_count == 0`): applies −10 to score, resets bank to 60 s, increments `player.overtime_count` to 1, returns `False`.
- Second overspend (`overtime_count > 0`): sets bank to 0 s, returns `True` — caller must end the game.

All three move handlers (`place_tiles`, `swap_tiles`, `pass_turn` at lines 154, 193, 220) now check this return value:

```python
if self._deduct_time(state, code):
    return await self._end_by_timeout(state, code, player_id)
```

`_end_by_timeout` at `game_service.py:346-356` is a private helper that writes the finished state and broadcasts without re-acquiring the lock (it is always called from within the lock scope). It creates a `Move` with `type=MoveType.TIMEOUT` and sets `state.phase = GamePhase.FINISHED`.

The background task (`_time_bank_task`) retains responsibility for the idle-timeout path — when a player simply runs the clock down without submitting any move. Its second-strike `else` branch at `game_service.py:337-344` was updated from `MoveType.FORFEIT` to `MoveType.TIMEOUT` for consistency.

`MoveType.TIMEOUT` was added to the `MoveType` enum in `packages/game-engine/src/game_engine/models.py:19`.

---

**Overtime notification — `stores/game.ts:46-56`**

The overtime event was previously invisible to users. `updateLocalState` in `stores/game.ts:46-71` was extended with a per-player `overtime_count` comparison on every incoming SSE payload. A module-level `previousOvertimeCounts: Record<string, number>` object tracks the last-seen count for each player UUID. When the transition from 0 to 1 is detected, a `'warning'` toast is fired:

```typescript
if (prevCount === 0 && player.overtime_count > 0) {
  addToast(`${player.nickname} ran out of time — −10 pts, +60s overtime`, 'warning')
}
```

`previousOvertimeCounts` is reset to `{}` inside `reset()` at `stores/game.ts:148` so it does not carry over to a subsequent game.

The `ToastMessage.type` union in `types/game.ts:104-108` was extended with `'warning'`. `ToastFooter.vue:24` was extended to render the warning dot in amber (`#f59e0b`), matching the overtime indicator colour used elsewhere.

---

**Forfeit notification — `stores/game.ts:58-69`**

A second block in `updateLocalState` fires a `'success'` toast when the game transitions to `finished` via a `forfeit` move and the forfeiting player is the opponent:

```typescript
if (payload.last_move?.type === 'forfeit') {
  const forfeiter = payload.players.find(p => p.id === payload.last_move?.player_id)
  if (forfeiter && forfeiter.id !== session.value?.player_id) {
    addToast(`${forfeiter.nickname} forfeited. You win!`, 'success')
  }
}
```

This fires before `game.value = payload` at line 70 updates the store, so it precedes the game-over card render by one reactive cycle.

---

**Distinct end-game cards — `GameView.vue:65-81`, `252-271`**

The game-over overlay previously rendered identically regardless of how the game ended. Three end reasons are now distinguished through an `endReason` computed at `GameView.vue:76-81`:

```typescript
const endReason = computed<'forfeit' | 'timeout' | 'normal'>(() => {
  const t = store.game?.last_move?.type
  if (t === 'forfeit') return 'forfeit'
  if (t === 'timeout') return 'timeout'
  return 'normal'
})
```

The `winner` computed at `GameView.vue:65-72` was extended to handle both `'forfeit'` and `'timeout'` move types: when either is the `last_move.type`, the winner is the player whose `id` does not match `last_move.player_id`.

The card headline at `GameView.vue:260` renders `'TIMED OUT'` in amber (`#f59e0b`) for the losing player on a timeout, and `'YOU WON'` for the winner. The subtitle at `GameView.vue:270` reads `'TIME OUT'` / `'FORFEITED'` / `'GAME OVER'` per `endReason`, coloured amber, tertiary red, and muted respectively.

---

**Stale `baseTimestamp` zeroing the non-active player's clock — `PlayerPanel.vue:40-48`**

When a player's turn ended, their clock stopped and `baseTimestamp` was left pointing at whatever moment the `time_remaining_secs` watcher last fired — typically when their turn began or when a previous SSE update changed their time value.

When the turn eventually returned to that player, `watch(() => props.isActiveTurn)` at `PlayerPanel.vue:40-48` called `startTicker()`. The interval function at line 27 immediately computed:

```typescript
const elapsed = (Date.now() - baseTimestamp) / 1000
displaySeconds.value = Math.max(0, Math.ceil(serverBase - elapsed))
```

`baseTimestamp` was potentially tens of seconds stale, so `elapsed` was large and `displaySeconds` collapsed to 0 on the first tick. This was especially visible in overtime: the non-active player held at 120 s but `baseTimestamp` pointed to a time from their previous turn.

The fix resets both `baseTimestamp` and `displaySeconds` inside the `isActiveTurn` watcher when a turn starts:

```typescript
watch(() => props.isActiveTurn, (active) => {
  if (active && props.player) {
    baseTimestamp = Date.now()
    displaySeconds.value = Math.ceil(serverBase)
    startTicker()
  } else {
    stopTicker()
  }
}, { immediate: true })
```

`serverBase` at the point `isActiveTurn` becomes `true` always holds the correct server-reported time from the most recent SSE update. Setting `displaySeconds.value = Math.ceil(serverBase)` snaps the display to the correct value before the first tick fires.

The `time_remaining_secs` watcher at `PlayerPanel.vue:32-38` continues to update `serverBase` and `baseTimestamp` whenever the server reports a new value — this handles the case where a player is already active and receives an updated time (e.g. entering overtime's 60 s extension).

---

### Decisions taken

**Decision 1: Overtime logic moved from background task to `_deduct_time` return value.**

The alternative was to prevent cancellation of the background task — for example by catching `asyncio.CancelledError` and applying the penalty before terminating. This was rejected because the task cancellation is intentional: `set_timer` cancels the old task to install a fresh one for the next player. A task that resists cancellation in order to apply a penalty would need to be distinguished from one that should silently terminate, complicating `game_manager`. Moving the logic into the synchronous move path makes it cancellation-proof by design and eliminates the need to reason about task scheduling order at all.

**Decision 2: `_end_by_timeout` extracted as a private method, not inlined.**

The timeout-end sequence (set phase, construct `TIMEOUT` move, save, broadcast, remove) is identical whether triggered from a move handler or the background task. Inlining it in all three move handlers would have created duplicated state mutation. The method is private and always called from inside the lock, so it does not need to acquire it.

**Decision 3: `previousOvertimeCounts` is a plain module-level object in the store, not a `ref`.**

The overtime count tracker does not need reactivity — it is read and written only inside `updateLocalState` and is never bound in a template. Using a plain `Record<string, number>` avoids the overhead of reactive wrapping and makes the intent explicit: this is internal bookkeeping, not display state.

**Decision 4: `baseTimestamp` reset on turn start, not only on server time change.**

The initial design assumed that a new SSE update would always change `time_remaining_secs` when a player's turn started, keeping `baseTimestamp` fresh. This assumption fails whenever a turn transitions without the non-active player's time changing — which is the normal case, since the backend only deducts from the active player's bank. The fix treats turn start as the canonical moment to reset the clock reference, making it independent of whether the server happened to send a new time value.

---

### Problems identified

**Problem 1: Play Again navigated without clearing store state.**

`handlePlayAgain` was missing from `GameView.vue`; the Play Again button called `router.push('/')` directly. The `finished` phase was left in the store, causing the game-over overlay to flash on the next mount.

*Location:* `frontend/src/views/GameView.vue` (old button `@click`).
*Resolution:* `handlePlayAgain()` at `GameView.vue:131-136` added. *Resolved.*

---

**Problem 2: `String(err)` on Error subclass includes class name.**

`ApiRequestError extends Error`. JavaScript's `Error.prototype.toString()` returns `"ClassName: message"`. All three catch blocks in `GameView.vue` used `String(err)`, surfacing `"ApiRequestError: ..."` to users.

*Location:* `frontend/src/views/GameView.vue:95,105,113`.
*Resolution:* Replaced with `err instanceof Error ? err.message : String(err)`. *Resolved.*

---

**Problem 3: Background timer cancellable at the instant of 0-second submission.**

A player could submit a move at exactly 0 seconds remaining. `set_timer` (called by `_start_timer` at the end of every move) cancelled the sleeping background task before it acquired the lock. The move proceeded without any time deduction.

*Location:* `packages/backend-api/src/backend_api/services/game_service.py:307-313` (`_start_timer` / `set_timer`), manifesting across `place_tiles` (L108), `swap_tiles` (L164), `pass_turn` (L203).
*Resolution:* `_deduct_time` at `game_service.py:281-305` now returns `bool` and applies overtime inline. All three move handlers check the return value. *Resolved.*

---

**Problem 4: Non-active player's clock displayed 0:00 immediately on turn start.**

`baseTimestamp` in `PlayerPanel.vue` was only updated by the `time_remaining_secs` watcher. A player whose bank did not change between turns (the non-active player) received no `baseTimestamp` update. On turn start, `startTicker` used a stale timestamp, computing a large elapsed value and clamping `displaySeconds` to 0.

*Location:* `frontend/src/components/ui/PlayerPanel.vue:40-48` (`watch(isActiveTurn)`).
*Resolution:* `baseTimestamp = Date.now()` and `displaySeconds.value = Math.ceil(serverBase)` added at the top of the `active` branch. *Resolved.*

---

**Problem 5: Overtime notification never shown; background task used wrong `MoveType`.**

The overtime event was broadcast via SSE but the frontend had no handler for it. Additionally, the background task's second-strike path used `MoveType.FORFEIT` instead of `MoveType.TIMEOUT`, making it impossible for the frontend to distinguish an idle timeout from a voluntary forfeit.

*Location:* `frontend/src/stores/game.ts` (`updateLocalState`), `packages/backend-api/src/backend_api/services/game_service.py:337-344` (`_time_bank_task` else-branch).
*Resolution:* `previousOvertimeCounts` tracking added in `game.ts:46-56`; background task updated to `MoveType.TIMEOUT` at `game_service.py:339`. *Resolved.*

---

### Current state of the codebase

**`packages/game-engine/`**

- `models.py`: `MoveType` enum now has five members: `PLACE`, `SWAP`, `PASS`, `FORFEIT`, `TIMEOUT`. `Player` carries `overtime_count: int = 0`. Fully implemented.

**`packages/backend-api/`**

- `services/game_service.py`: All three active move handlers check `_deduct_time` return value and call `_end_by_timeout` on second overspend. Background task handles the idle path. Both paths emit `MoveType.TIMEOUT`. Fully implemented.
- Other backend modules unchanged.

**`frontend/src/`**

- `types/game.ts`: `MoveType` includes `'timeout'`. `ToastMessage.type` includes `'warning'`. Fully aligned with backend.
- `stores/game.ts`: `updateLocalState` fires overtime and forfeit toasts. `reset()` clears `previousOvertimeCounts`. Fully implemented.
- `components/ui/ToastFooter.vue`: Amber dot for `'warning'` toasts. Fully implemented.
- `components/ui/PlayerPanel.vue`: `baseTimestamp` reset on turn start. Both watchers (`time_remaining_secs`, `isActiveTurn`) cooperate correctly. Fully implemented.
- `views/GameView.vue`: `handlePlayAgain` clears store. Error messages extracted with `instanceof` guard. `endReason` computed drives distinct card variants. `winner` handles `forfeit` and `timeout` move types. Fully implemented.

---

### Open questions

1. The background timer in `_time_bank_task` applies overtime by directly mutating `state` and saving — it does not go through `_deduct_time`. If the two paths ever diverge (e.g. a change to the penalty amount or the 60 s grace period), they would fall out of sync silently. Should the idle-timeout path call `_deduct_time` as well, or is the task's internal logic acceptable as a second implementation?

2. `previousOvertimeCounts` in `game.ts` is keyed on `player.id` (UUID string). If the same player UUID appeared in two different games (which the current UUID generation makes astronomically unlikely but not impossible), the initial count lookup on the second game could return a stale `1` and suppress the first-strike toast. Is this risk worth addressing, or is UUID collision acceptable given the session lifecycle?

3. The `_time_bank_task` fires a second `asyncio.create_task` for the overtime extension (`game_service.py:332-335`). If the server restarts between the two tasks, the overtime extension task is lost and the player's clock never expires. There is currently no mechanism to recover in-flight timers from Redis on restart. Is this a known accepted risk?

---

### References

| File | Key locations |
|---|---|
| `packages/game-engine/src/game_engine/models.py` | `MoveType` enum (L14–19), `Player` dataclass (L49–57), `GameState` dataclass (L62–74) |
| `packages/backend-api/src/backend_api/services/game_service.py` | `place_tiles` (L108–162), `swap_tiles` (L164–201), `pass_turn` (L203–228), `forfeit` (L230–242), `_deduct_time` (L281–305), `_start_timer` (L307–313), `_time_bank_task` (L315–344), `_end_by_timeout` (L346–356) |
| `frontend/src/types/game.ts` | `MoveType` (L22), `ToastMessage` (L104–108) |
| `frontend/src/stores/game.ts` | `updateLocalState` (L46–71), `previousOvertimeCounts` (L26), `reset` (L143–149) |
| `frontend/src/components/ui/ToastFooter.vue` | Warning dot colour (L24) |
| `frontend/src/components/ui/PlayerPanel.vue` | `time_remaining_secs` watcher (L32–38), `isActiveTurn` watcher (L40–48), `startTicker` (L24–29) |
| `frontend/src/views/GameView.vue` | `winner` computed (L65–72), `endReason` computed (L76–81), `handleSubmit` catch (L94–95), `handlePass` catch (L104–105), `handleForfeit` catch (L112–113), `handlePlayAgain` (L131–136), game-over card (L252–271) |
