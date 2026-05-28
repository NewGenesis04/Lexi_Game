<script setup lang="ts">
import { ref } from 'vue'
import type { MovePayload } from '../../types/game'
import { useGameStore } from '../../stores/game'

const props = defineProps<{
  code: string
  hasPlacements: boolean
  hasSwaps: boolean
  swapMode: boolean
}>()

const emit = defineEmits<{
  clear: []
  submit: [payload: MovePayload]
  toggleSwap: []
}>()

const store = useGameStore()
const loading = ref(false)

async function handleSubmit() {
  if (!props.hasPlacements && !props.hasSwaps) return
  loading.value = true
  try {
    await store.submitMove(props.code, { type: props.hasPlacements ? 'place' : 'swap' })
  } catch (err) {
    store.addToast(String(err), 'error')
  } finally {
    loading.value = false
  }
}

async function handlePass() {
  loading.value = true
  try {
    await store.submitMove(props.code, { type: 'pass' })
  } catch (err) {
    store.addToast(String(err), 'error')
  } finally {
    loading.value = false
  }
}

async function handleForfeit() {
  loading.value = true
  try {
    await store.forfeit(props.code)
  } catch (err) {
    store.addToast(String(err), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-center gap-2">
    <button
      v-if="hasPlacements || hasSwaps"
      :disabled="loading"
      class="rounded bg-blue-600 px-4 py-2 text-sm font-medium transition hover:bg-blue-700 disabled:opacity-50"
      @click="handleSubmit"
    >
      {{ loading ? 'Submitting...' : hasPlacements ? 'Submit' : 'Swap' }}
    </button>
    <button
      v-if="hasPlacements"
      :disabled="loading"
      class="rounded bg-neutral-600 px-3 py-2 text-sm transition hover:bg-neutral-500 disabled:opacity-50"
      @click="emit('clear')"
    >
      Clear
    </button>
    <button
      :class="swapMode ? 'rounded bg-yellow-600 px-3 py-2 text-sm transition hover:bg-yellow-700' : 'rounded bg-neutral-600 px-3 py-2 text-sm transition hover:bg-neutral-500'"
      :disabled="loading || hasPlacements"
      @click="emit('toggleSwap')"
    >
      {{ swapMode ? 'Cancel Swap' : 'Swap' }}
    </button>
    <button
      :disabled="loading"
      class="rounded bg-neutral-600 px-3 py-2 text-sm transition hover:bg-neutral-500 disabled:opacity-50"
      @click="handlePass"
    >
      Pass
    </button>
    <button
      :disabled="loading"
      class="rounded bg-red-700 px-3 py-2 text-sm transition hover:bg-red-800 disabled:opacity-50"
      @click="handleForfeit"
    >
      Forfeit
    </button>
  </div>
</template>
