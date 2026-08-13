<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { theme, toggle } = useTheme()
</script>

<template>
  <main class="relative min-h-dvh bg-lexi-bg text-lexi-text">
    <button
      class="fixed top-4 right-4 w-9 h-9 flex items-center justify-center bg-transparent border-lexi border-lexi-border shadow-lexi-sm text-lexi-text transition-all duration-lexi-base hover:shadow-lexi-md hover:-translate-x-px hover:-translate-y-px active:shadow-lexi-pressed active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
      :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      @click="toggle"
    >
      <svg v-if="theme === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>

    <div class="mx-auto max-w-2xl px-6 py-16">
      <h1 class="font-lexi-ui text-lexi-2xl font-bold tracking-lexi-wide mb-1">LEXI</h1>
      <p class="font-lexi-ui text-lexi-sm tracking-lexi-wide text-lexi-text-muted uppercase mb-10">Rules</p>

      <!-- Objective -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">Objective</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary">
          Take turns placing letter tiles on the board to form words, crossword-style. Every word must be
          valid in the dictionary the game was created with — there's no challenge mechanic, the dictionary
          decides. Highest score wins, with a couple of exceptions below.
        </p>
      </section>

      <!-- The board -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">The Board</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary mb-3">
          A standard 15×15 grid. The first word of the game must cross the center square. Every word after
          that must connect to a tile already on the board. Premium squares multiply the score of a letter
          or the whole word, but only the first time a tile lands on them:
        </p>
        <div class="grid grid-cols-2 gap-2 font-lexi-ui text-lexi-sm">
          <div class="flex items-center gap-2 px-3 py-2 border-lexi-light border-lexi-border">
            <span class="flex items-center justify-center w-8 h-8 flex-shrink-0 font-black text-lexi-xs bg-lexi-sq-tw text-lexi-sq-tw-label">TW</span> Triple Word
          </div>
          <div class="flex items-center gap-2 px-3 py-2 border-lexi-light border-lexi-border">
            <span class="flex items-center justify-center w-8 h-8 flex-shrink-0 font-black text-lexi-xs bg-lexi-sq-dw text-lexi-sq-dw-label">DW</span> Double Word
          </div>
          <div class="flex items-center gap-2 px-3 py-2 border-lexi-light border-lexi-border">
            <span class="flex items-center justify-center w-8 h-8 flex-shrink-0 font-black text-lexi-xs bg-lexi-sq-tl text-lexi-sq-tl-label">TL</span> Triple Letter
          </div>
          <div class="flex items-center gap-2 px-3 py-2 border-lexi-light border-lexi-border">
            <span class="flex items-center justify-center w-8 h-8 flex-shrink-0 font-black text-lexi-xs bg-lexi-sq-dl text-lexi-sq-dl-label">DL</span> Double Letter
          </div>
        </div>
      </section>

      <!-- Tiles -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">Tiles</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary">
          100 tiles in the bag, the standard Scrabble distribution — including 2 blanks worth 0 points that
          can stand in for any letter. Each player starts with a 7-tile rack and draws back up to 7 after
          every placement or swap.
        </p>
      </section>

      <!-- Taking a turn -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">Taking a Turn</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary mb-2">
          On your turn, do exactly one of:
        </p>
        <ul class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary list-disc pl-5 space-y-1">
          <li><strong class="text-lexi-text">Place</strong> tiles from your rack to form one or more valid words.</li>
          <li><strong class="text-lexi-text">Swap</strong> any number of tiles for fresh ones from the bag — doesn't score, but refreshes a stuck rack.</li>
          <li><strong class="text-lexi-text">Pass</strong> if you have no play you want to make.</li>
        </ul>
      </section>

      <!-- Scoring -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">Scoring</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary">
          Sum each tile's point value, apply any letter/word premiums the new tiles land on, and add it all
          up across every word formed that turn. Using all 7 tiles from your rack in a single placement
          earns a <strong class="text-lexi-text">+50 point bonus</strong>.
        </p>
      </section>

      <!-- Clock -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">The Clock</h2>
        <p class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary">
          Each player has a shared bank of time for the whole game, not per turn. Every action — placing,
          swapping, or passing, valid or not — spends real time off your bank. Run it out and you get an
          <strong class="text-lexi-text">overtime grant</strong>: −10 points, and your bank resets to 60
          seconds. You get 3 of these. Run out a 4th time and you lose immediately, regardless of score.
        </p>
      </section>

      <!-- Ending the game -->
      <section class="mb-8">
        <h2 class="font-lexi-ui text-lexi-base font-black tracking-lexi-wide uppercase text-lexi-active mb-3">Ending the Game</h2>
        <ul class="font-lexi-display text-lexi-md leading-relaxed text-lexi-text-secondary list-disc pl-5 space-y-2">
          <li>
            <strong class="text-lexi-text">Someone empties their rack with the bag empty</strong> — the game
            ends, each opponent's remaining tile points are deducted from their score and awarded to the
            player who went out. Highest score wins.
          </li>
          <li>
            <strong class="text-lexi-text">Six consecutive passes</strong> (three full round-trips with no
            placement or swap in between) — the game ends there, everyone's rack points are deducted from
            their own score, and highest score wins. Any placement or swap resets this counter, so passing
            once is never risky by itself.
          </li>
          <li>
            <strong class="text-lexi-text">A player runs out of time or forfeits</strong> — the other player
            wins outright, regardless of the score at that point.
          </li>
        </ul>
      </section>
    </div>
  </main>
</template>
