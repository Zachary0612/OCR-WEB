import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('./views/Home.vue') },
  { path: '/search', name: 'Search', component: () => import('./views/Search.vue') },
  { path: '/result/:id', name: 'Result', component: () => import('./views/Result.vue'), props: true },
  { path: '/batch-insights/:batchId', name: 'BatchInsights', component: () => import('./views/BatchInsights.vue'), props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
