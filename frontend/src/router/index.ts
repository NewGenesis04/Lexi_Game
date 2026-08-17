import { createRouter, createWebHistory } from 'vue-router'
import { gameGuard } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'lobby',
      component: () => import('../views/LobbyView.vue'),
    },
    {
      path: '/game/:code',
      name: 'game',
      component: () => import('../views/GameView.vue'),
      beforeEnter: gameGuard,
    },
    {
      path: '/rules',
      name: 'rules',
      component: () => import('../views/RulesView.vue'),
    },
  ],
})

export default router
