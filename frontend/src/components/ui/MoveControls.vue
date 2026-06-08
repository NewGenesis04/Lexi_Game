<script setup lang="ts">
const props = defineProps<{
  code: string
  hasPlacements: boolean
  hasSwaps: boolean
  swapMode: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  submit: []
  clear: []
  pass: []
  forfeit: []
  toggleSwap: []
}>()

function handleSubmit() {
  if (!props.hasPlacements && !props.hasSwaps) return
  emit('submit')
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-center gap-2">
    <!-- Primary action: submit word or confirm swap -->
    <button
      v-if="hasPlacements || hasSwaps"
      :disabled="loading"
      class="px-5 py-2 bg-lexi-primary text-lexi-text-on-accent border-lexi border-lexi-border shadow-lexi-md font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase cursor-pointer transition-all duration-lexi-base hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
      @click="handleSubmit"
    >
      {{ loading ? 'SUBMITTING…' : hasPlacements ? 'SUBMIT' : 'SWAP' }}
    </button>

    <!-- Clear placed tiles -->
    <button
      v-if="hasPlacements"
      :disabled="loading"
      class="px-4 py-2 bg-transparent text-lexi-text-secondary border-lexi border-lexi-border-muted font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase cursor-pointer transition-all duration-lexi-base hover:border-lexi-border hover:text-lexi-text disabled:opacity-40 disabled:cursor-not-allowed"
      @click="emit('clear')"
    >
      CLEAR
    </button>

    <!-- Swap mode toggle -->
    <button
      :class="[
        'px-4 py-2 border-lexi font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase cursor-pointer transition-all duration-lexi-base disabled:opacity-40 disabled:cursor-not-allowed',
        swapMode
          ? 'bg-lexi-primary text-lexi-text-on-accent border-lexi-border shadow-lexi-pressed translate-x-0.5 translate-y-0.5'
          : 'bg-transparent text-lexi-text-secondary border-lexi-border-muted hover:border-lexi-border hover:text-lexi-text'
      ]"
      :disabled="loading || hasPlacements"
      @click="emit('toggleSwap')"
    >
      {{ swapMode ? 'CANCEL' : 'SWAP' }}
    </button>

    <!-- Pass turn -->
    <button
      :disabled="loading"
      class="px-4 py-2 bg-transparent text-lexi-text-secondary border-lexi border-lexi-border-muted font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase cursor-pointer transition-all duration-lexi-base hover:border-lexi-border hover:text-lexi-text disabled:opacity-40 disabled:cursor-not-allowed"
      @click="emit('pass')"
    >
      PASS
    </button>

    <!-- Forfeit (ghost danger) -->
    <button
      :disabled="loading"
      class="px-4 py-2 bg-transparent text-lexi-danger border-lexi border-lexi-danger font-lexi-ui text-lexi-xs font-black tracking-lexi-wide uppercase cursor-pointer transition-all duration-lexi-base hover:bg-lexi-danger-subtle disabled:opacity-40 disabled:cursor-not-allowed"
      @click="emit('forfeit')"
    >
      FORFEIT
    </button>
  </div>
</template>
