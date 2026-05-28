<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

const store = useGameStore()
const router = useRouter()

const tab = ref<'create' | 'join'>('create')
const nickname = ref('')
const timeLimit = ref(300)
const dictionary = ref<'TWL06' | 'CSW21'>('TWL06')
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
  <main class="flex min-h-screen items-center justify-center" style="background: var(--color-surface);">
    <div
      class="w-full max-w-md p-8"
      style="
        background: var(--color-primary-container);
        border-radius: 0.5rem;
        border: 1px solid var(--color-outline);
        box-shadow: var(--shadow-card);
      "
    >
      <h1
        class="text-center mb-6"
        style="font-family: var(--font-serif); font-size: 32px; font-weight: 500; line-height: 1.2; color: var(--color-primary);"
      >
        NEO SCRABBLE
      </h1>

      <div
        class="flex rounded-sm mb-6"
        style="background: var(--color-surface-container-lowest); padding: 2px;"
      >
        <button
          :style="{
            background: tab === 'create' ? 'var(--color-outline)' : 'transparent',
            color: tab === 'create' ? 'var(--color-surface-container-lowest)' : 'var(--color-on-surface-variant)',
          }"
          class="flex-1 rounded px-4 py-2 transition"
          style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer;"
          @click="tab = 'create'"
        >
          Create
        </button>
        <button
          :style="{
            background: tab === 'join' ? 'var(--color-outline)' : 'transparent',
            color: tab === 'join' ? 'var(--color-surface-container-lowest)' : 'var(--color-on-surface-variant)',
          }"
          class="flex-1 rounded px-4 py-2 transition"
          style="font-family: var(--font-sans); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer;"
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
          class="w-full"
          style="
            background: var(--color-surface-container-lowest);
            color: var(--color-on-surface);
            border: 1px solid var(--color-outline-variant);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-serif);
            font-size: 18px;
            outline: none;
          "
        />
        <select
          v-model="dictionary"
          class="w-full"
          style="
            background: var(--color-surface-container-lowest);
            color: var(--color-on-surface);
            border: 1px solid var(--color-outline-variant);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            outline: none;
          "
        >
          <option value="TWL06">North American (TWL)</option>
          <option value="CSW21">International (CSW21)</option>
        </select>
        <select
          v-model="timeLimit"
          class="w-full"
          style="
            background: var(--color-surface-container-lowest);
            color: var(--color-on-surface);
            border: 1px solid var(--color-outline-variant);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            outline: none;
          "
        >
          <option :value="300">5 min per player</option>
          <option :value="600">10 min per player</option>
          <option :value="900">15 min per player</option>
          <option :value="1200">20 min per player</option>
          <option :value="1800">30 min per player</option>
        </select>
        <button
          :disabled="loading"
          class="w-full"
          style="
            background: linear-gradient(180deg, var(--color-outline), #8a7d7b);
            color: var(--color-surface-container-lowest);
            border: none;
            box-shadow: var(--shadow-button-filled);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            cursor: pointer;
            transition: all 0.2s;
          "
          @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
          @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
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
          class="w-full"
          style="
            background: var(--color-surface-container-lowest);
            color: var(--color-on-surface);
            border: 1px solid var(--color-outline-variant);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border-radius: 0.25rem;
            padding: 12px 16px;
            text-align: center;
            font-family: var(--font-sans);
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 0.3em;
            outline: none;
          "
        />
        <input
          v-model="nickname"
          placeholder="Your nickname"
          required
          class="w-full"
          style="
            background: var(--color-surface-container-lowest);
            color: var(--color-on-surface);
            border: 1px solid var(--color-outline-variant);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-serif);
            font-size: 18px;
            outline: none;
          "
        />
        <button
          :disabled="loading"
          class="w-full"
          style="
            background: linear-gradient(180deg, var(--color-outline), #8a7d7b);
            color: var(--color-surface-container-lowest);
            border: none;
            box-shadow: var(--shadow-button-filled);
            border-radius: 0.25rem;
            padding: 12px 16px;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            cursor: pointer;
            transition: all 0.2s;
          "
          @mouseenter="(e: any) => { e.target.style.opacity = '0.85' }"
          @mouseleave="(e: any) => { e.target.style.opacity = '1' }"
        >
          {{ loading ? 'Joining...' : 'Join Game' }}
        </button>
      </form>
    </div>
  </main>
</template>
