<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useTheme } from '../composables/useTheme'
import { AVATARS, AVATAR_KEYS } from '../constants/avatars'

const store = useGameStore()
const router = useRouter()
const { theme, toggle } = useTheme()

const tab = ref<'create' | 'join'>('create')
const nickname = ref('')
const timeLimit = ref(300)
const dictionary = ref<'TWL06' | 'CSW21'>('TWL06')
const joinCode = ref('')
const loading = ref(false)
const error = ref('')
const selectedAvatar = ref<string>(
  AVATAR_KEYS[Math.floor(Math.random() * AVATAR_KEYS.length)]
)

async function handleCreate() {
  loading.value = true
  error.value = ''
  try {
    const res = await store.createGame(nickname.value.trim(), timeLimit.value, dictionary.value, selectedAvatar.value)
    router.push(`/game/${res.code}`)
  } catch (err) {
    console.error('[Lexi] create game failed', err)
    error.value = err instanceof Error ? err.message : 'Something went wrong'
  } finally {
    loading.value = false
  }
}

async function handleJoin() {
  loading.value = true
  error.value = ''
  try {
    await store.joinGame(joinCode.value, nickname.value.trim(), selectedAvatar.value)
    router.push(`/game/${joinCode.value}`)
  } catch (err) {
    console.error('[Lexi] join game failed', err)
    error.value = err instanceof Error ? err.message : 'Something went wrong'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="relative flex min-h-screen items-center justify-center bg-lexi-bg">

    <!-- Theme toggle -->
    <button
      class="absolute top-4 right-4 w-9 h-9 flex items-center justify-center bg-transparent border-lexi border-lexi-border shadow-lexi-sm text-lexi-text transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
      :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      @click="toggle"
    >
      <!-- Sun (shown in dark mode — click to go light) -->
      <svg v-if="theme === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
      <!-- Moon (shown in light mode — click to go dark) -->
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>

    <div class="w-full max-w-sm bg-lexi-bg-elevated border-lexi border-lexi-border shadow-lexi-lg p-8">

      <h1 class="font-lexi-ui text-lexi-2xl text-lexi-text text-center mb-6 font-bold tracking-lexi-wide">
        LEXI
      </h1>

      <!-- Avatar picker -->
      <div class="grid grid-cols-5 gap-1 mb-6">
        <button
          v-for="key in AVATAR_KEYS"
          :key="key"
          type="button"
          :class="[
            'w-full aspect-square overflow-hidden transition-all duration-lexi-fast cursor-pointer p-0',
            selectedAvatar === key
              ? 'border-lexi border-lexi-primary shadow-lexi-sm -translate-x-px -translate-y-px'
              : 'border-lexi-light border-lexi-border-muted hover:border-lexi-border'
          ]"
          @click="selectedAvatar = key"
        >
          <img :src="AVATARS[key]" :alt="key" class="w-full h-full object-cover" draggable="false" />
        </button>
      </div>

      <!-- Tab switcher -->
      <div class="flex border-lexi border-lexi-border mb-6">
        <button
          :class="tab === 'create'
            ? 'bg-lexi-primary text-lexi-text-on-accent'
            : 'bg-transparent text-lexi-text-secondary hover:bg-lexi-bg-sunken'"
          class="flex-1 py-2 font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold border-r border-lexi-border transition-colors duration-lexi-fast cursor-pointer"
          @click="tab = 'create'"
        >
          CREATE
        </button>
        <button
          :class="tab === 'join'
            ? 'bg-lexi-primary text-lexi-text-on-accent'
            : 'bg-transparent text-lexi-text-secondary hover:bg-lexi-bg-sunken'"
          class="flex-1 py-2 font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-colors duration-lexi-fast cursor-pointer"
          @click="tab = 'join'"
        >
          JOIN
        </button>
      </div>

      <!-- Create form -->
      <form v-if="tab === 'create'" class="flex flex-col gap-4" @submit.prevent="handleCreate">
        <input
          v-model="nickname"
          placeholder="YOUR NAME"
          maxlength="10"
          required
          class="w-full px-3 py-2 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-base tracking-lexi-ui placeholder:text-lexi-text-muted focus:outline-none focus:shadow-lexi-md focus:-translate-x-px focus:-translate-y-px transition-all duration-lexi-fast"
        />
        <select
          v-model="dictionary"
          class="w-full px-3 py-2 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-ui focus:outline-none focus:shadow-lexi-md transition-all duration-lexi-fast cursor-pointer"
        >
          <option value="TWL06">North American (TWL)</option>
          <option value="CSW21">International (CSW21)</option>
        </select>
        <select
          v-model="timeLimit"
          class="w-full px-3 py-2 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-sm tracking-lexi-ui focus:outline-none focus:shadow-lexi-md transition-all duration-lexi-fast cursor-pointer"
        >
          <option :value="300">5 min per player</option>
          <option :value="600">10 min per player</option>
          <option :value="900">15 min per player</option>
          <option :value="1200">20 min per player</option>
          <option :value="1800">30 min per player</option>
        </select>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 bg-lexi-primary text-lexi-text-on-accent border-lexi border-lexi-border shadow-lexi-md font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0 cursor-pointer"
        >
          {{ loading ? 'CREATING...' : 'CREATE GAME' }}
        </button>
      </form>

      <!-- Join form -->
      <form v-if="tab === 'join'" class="flex flex-col gap-4" @submit.prevent="handleJoin">
        <input
          v-model="joinCode"
          placeholder="GAME CODE"
          required
          maxlength="6"
          autocapitalize="characters"
          class="w-full px-3 py-2 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-base tracking-lexi-wide text-center uppercase placeholder:text-lexi-text-muted placeholder:normal-case focus:outline-none focus:shadow-lexi-md focus:-translate-x-px focus:-translate-y-px transition-all duration-lexi-fast"
          @input="joinCode = joinCode.toUpperCase()"
        />
        <input
          v-model="nickname"
          placeholder="YOUR NAME"
          maxlength="10"
          required
          class="w-full px-3 py-2 bg-lexi-bg-sunken text-lexi-text border-lexi border-lexi-border shadow-lexi-sm font-lexi-ui text-lexi-base tracking-lexi-ui placeholder:text-lexi-text-muted focus:outline-none focus:shadow-lexi-md focus:-translate-x-px focus:-translate-y-px transition-all duration-lexi-fast"
        />
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 bg-lexi-primary text-lexi-text-on-accent border-lexi border-lexi-border shadow-lexi-md font-lexi-ui text-lexi-sm tracking-lexi-wide uppercase font-bold transition-all duration-lexi-base hover:shadow-lexi-lg hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0 cursor-pointer"
        >
          {{ loading ? 'JOINING...' : 'JOIN GAME' }}
        </button>
      </form>

      <!-- Inline error -->
      <p
        v-if="error"
        class="mt-4 font-lexi-ui text-lexi-xs tracking-lexi-ui text-lexi-danger text-center"
      >
        {{ error }}
      </p>

    </div>
  </main>
</template>
