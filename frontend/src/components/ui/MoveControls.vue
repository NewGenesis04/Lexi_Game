<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  code: string
  hasPlacements: boolean
  hasSwaps: boolean
  swapMode: boolean
}>()

const emit = defineEmits<{
  submit: []
  clear: []
  pass: []
  forfeit: []
  toggleSwap: []
}>()

const loading = ref(false)

async function handleSubmit() {
  if (!props.hasPlacements && !props.hasSwaps) return
  loading.value = true
  emit('submit')
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-center gap-2">
    <button
      v-if="hasPlacements || hasSwaps"
      :disabled="loading"
      class="btn btn--submit"
      @click="handleSubmit"
    >
      {{ loading ? 'Submitting...' : hasPlacements ? 'Submit' : 'Swap' }}
    </button>
    <button
      v-if="hasPlacements"
      :disabled="loading"
      class="btn btn--outline"
      @click="emit('clear')"
    >
      Clear
    </button>
    <button
      :class="['btn', swapMode ? 'btn--swap-active' : 'btn--outline']"
      :disabled="loading || hasPlacements"
      @click="emit('toggleSwap')"
    >
      {{ swapMode ? 'Cancel Swap' : 'Swap' }}
    </button>
    <button
      :disabled="loading"
      class="btn btn--outline"
      @click="emit('pass')"
    >
      Pass
    </button>
    <button
      :disabled="loading"
      class="btn btn--forfeit"
      @click="emit('forfeit')"
    >
      Forfeit
    </button>
  </div>
</template>

<style scoped>
.btn {
  border-radius: 0.25rem;
  padding: 8px 16px;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}
.btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn--submit {
  padding: 8px 20px;
  background: linear-gradient(180deg, var(--color-outline), #8a7d7b);
  color: var(--color-surface-container-lowest);
  box-shadow: var(--shadow-button-filled);
}
.btn--submit:hover:not(:disabled) {
  opacity: 0.85;
}

.btn--outline {
  background: transparent;
  color: var(--color-on-surface-variant);
  border: 1px solid var(--color-outline-variant);
}
.btn--outline:hover:not(:disabled) {
  background: var(--color-surface-container-high);
}

.btn--swap-active {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
.btn--swap-active:hover:not(:disabled) {
  background: rgba(227, 190, 184, 0.1);
}

.btn--forfeit {
  background: var(--color-tertiary-container);
  color: var(--color-tertiary);
  border: 1px solid var(--color-tertiary);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
.btn--forfeit:hover:not(:disabled) {
  opacity: 0.85;
}
</style>
