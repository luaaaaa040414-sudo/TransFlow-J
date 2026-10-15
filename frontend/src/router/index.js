import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'pipeline', component: () => import('../views/PipelineView.vue'), meta: { title: '流水线总览' } },
  { path: '/prep', name: 'prep', component: () => import('../views/PrepView.vue'), meta: { title: '译前准备' } },
  { path: '/sources', name: 'sources', component: () => import('../views/SourcesView.vue'), meta: { title: '信源分级' } },
  { path: '/journals', name: 'journals', component: () => import('../views/JournalsView.vue'), meta: { title: '期刊风格库' } },
  { path: '/review', name: 'review', component: () => import('../views/ReviewView.vue'), meta: { title: '校对反思' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
