import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '学术中译英质量保障平台 - 项目介绍与方法论' }
  },
  {
    path: '/workspace',
    name: 'Workspace',
    component: () => import('../views/WorkspaceView.vue'),
    meta: { title: '论文翻译工作台' }
  },
  {
    path: '/projects',
    redirect: '/workspace'
  },
  {
    path: '/project/:id',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectDetailView.vue'),
    meta: { title: '项目详情' }
  },
  {
    path: '/project/:id/terminology',
    name: 'Terminology',
    component: () => import('../views/TerminologyView.vue'),
    meta: { title: '术语查证' }
  },
  {
    path: '/project/:id/translate',
    name: 'Translate',
    component: () => import('../views/TranslateView.vue'),
    meta: { title: '翻译工作台' }
  },
  {
    path: '/project/:id/proofread',
    name: 'Proofread',
    component: () => import('../views/ProofreadView.vue'),
    meta: { title: '校对与报告' }
  },
  {
    path: '/journals',
    name: 'Journals',
    component: () => import('../views/JournalsView.vue'),
    meta: { title: '期刊库' }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('../views/ModelsView.vue'),
    meta: { title: '模型配置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = (to.meta.title as string) || '学术中译英质量保障平台'
})

export default router
