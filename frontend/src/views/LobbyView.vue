<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

const store = useGameStore()
const router = useRouter()

const tab = ref<'create' | 'join'>('create')
const nickname = ref('')
const timeLimit = ref(300)
const dictionary = ref<'TWL' | 'CSW21'>('TWL')
const joinCode = ref('')
const loading = ref(false)

async function handleCreate() {
  loading.value = true
  try {
    const res = await store.createGame(nickname.value, timeLimit.value, dictionary.value)
    store.connectSSEStream()
    router.push(`/game/${res.code}`)
  } catch (err) {
    store.addToast(String(err), 'error')
  } finally {
    loading.value = false
  }
}

async function handleJoin() {
  loading.value = true
  try {
    await store.joinGame(joinCode.value, nickname.value)
    store.connectSSEStream()
    router.push(`/game/${joinCode.value}`)
  } catch (err) {
    store.addToast(String(err), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-neutral-900 text-white">
    <div class="w-full max-w-md space-y-6 rounded-lg bg-neutral-800 p-8 shadow-xl">
      <h1 class="text-center text-3xl font-bold tracking-tight">NEO SCRABBLE</h1>

      <div class="flex rounded-md bg-neutral-700 p-1">
        <button
          :class="tab === 'create' ? 'bg-neutral-600 text-white' : 'text-neutral-400'"
          class="flex-1 rounded px-4 py-2 text-sm font-medium transition"
          @click="tab = 'create'"
        >
          Create
        </button>
        <button
          :class="tab === 'join' ? 'bg-neutral-600 text-white' : 'text-neutral-400'"
          class="flex-1 rounded px-4 py-2 text-sm font-medium transition"
          @click="tab = 'join'"
        >
          Join
        </button>
      </div>

      <form
        v-if="tab === 'create'"
        class="space-y-4"
        @submit.prevent="handleCreate"
      >
        <input
          v-model="nickname"
          placeholder="Your nickname"
          required
          class="w-full rounded border border-neutral-600 bg-neutral-700 px-3 py-2 text-white placeholder-neutral-400 focus:border-blue-500 focus:outline-none"
        />
        <select
          v-model="dictionary"
          class="w-full rounded border border-neutral-600 bg-neutral-700 px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
        >
          <option value="TWL">North American (TWL)</option>
          <option value="CSW21">International (CSW21)</option>
        </select>
        <select
          v-model="timeLimit"
          class="w-full rounded border border-neutral-600 bg-neutral-700 px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
        >
          <option :value="60">1 min per player</option>
          <option :value="180">3 min per player</option>
          <option :value="300">5 min per player</option>
          <option :value="600">10 min per player</option>
        </select>
        <button
          :disabled="loading"
          class="w-full rounded bg-blue-600 px-4 py-2 font-medium transition hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Creating...' : 'Create Game' }}
        </button>
      </form>

      <form
        v-if="tab === 'join'"
        class="space-y-4"
        @submit.prevent="handleJoin"
      >
        <input
          v-model="joinCode"
          placeholder="6-digit game code"
          required
          maxlength="6"
          class="w-full rounded border border-neutral-600 bg-neutral-700 px-3 py-2 text-white placeholder-neutral-400 focus:border-blue-500 focus:outline-none"
        />
        <input
          v-model="nickname"
          placeholder="Your nickname"
          required
          class="w-full rounded border border-neutral-600 bg-neutral-700 px-3 py-2 text-white placeholder-neutral-400 focus:border-blue-500 focus:outline-none"
        />
        <button
          :disabled="loading"
          class="w-full rounded bg-green-600 px-4 py-2 font-medium transition hover:bg-green-700 disabled:opacity-50"
        >
          {{ loading ? 'Joining...' : 'Join Game' }}
        </button>
      </form>
    </div>
  </main>
</template>
