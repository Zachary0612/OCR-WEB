import { createRouter, createWebHistory } from 'vue-router'
import { useAuthState } from './composables/useAuthState.js'

const routes = [
  { path: '/', name: 'Home', component: () => import('./views/Home.vue') },
  { path: '/search', name: 'Search', component: () => import('./views/Search.vue') },
  { path: '/result/:id', name: 'Result', component: () => import('./views/Result.vue'), props: true },
  { path: '/batch-insights/:batchId', name: 'BatchInsights', component: () => import('./views/BatchInsights.vue'), props: true },
  { path: '/login', name: 'Login', component: () => import('./views/Login.vue'), meta: { public: true } },
  { path: '/register', name: 'Register', component: () => import('./views/Register.vue'), meta: { public: true } },
  { path: '/admin/review', name: 'AdminReview', component: () => import('./views/AdminReview.vue'), meta: { requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const authState = useAuthState()

router.beforeEach(async (to) => {
  const status = await authState.refreshAuthStatus()
  if (!status.enabled) {
    if (to.name === 'Login' || to.name === 'Register') {
      return { name: 'Home' }
    }
    return true
  }

  if (!status.authenticated) {
    if (to.meta?.public) return true
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'Login' || to.name === 'Register') {
    const redirectTarget = String(to.query?.redirect || '/')
    return redirectTarget || '/'
  }

  if (to.meta?.requiresAdmin && !status.is_admin) {
    return { name: 'Home' }
  }

  return true
})

export default router
