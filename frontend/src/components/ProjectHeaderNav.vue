<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { projectsApi } from '../api'
const props = defineProps<{
  projectId: number | string
  currentTab: 'overview' | 'terminology' | 'translate' | 'proofread'
  projectName?: string
}>()
const fetchedName = ref('')
const displayName = computed(() => props.projectName || fetchedName.value || `项目 ${props.projectId}`)
const steps = [
  { key: 'overview', number: '01', label: '原文与要求', suffix: '' },
  { key: 'terminology', number: '02', label: '术语查证', suffix: '/terminology' },
  { key: 'translate', number: '03', label: '逐段翻译', suffix: '/translate' },
  { key: 'proofread', number: '04', label: '校对与报告', suffix: '/proofread' },
]
const hints = {
  overview: '先上传中文文稿，再选择目标期刊和翻译要求。',
  terminology: '确认关键词的译法与信源，再带着术语表进入翻译。',
  translate: '逐段对照原文与译文，保存修改后进入校对。',
  proofread: '检查译文，处理审校意见，再导出成果。',
}
onMounted(async () => {
  if (!props.projectName && props.projectId) {
    try { const res = await projectsApi.get(Number(props.projectId)); fetchedName.value = res?.name || '' } catch { /* Parent view handles project-load errors. */ }
  }
})
</script>

<template>
  <div class="project-header-nav">
    <div class="project-breadcrumb"><router-link to="/workspace">我的项目</router-link><span aria-hidden="true">/</span><span class="project-name" :title="displayName">{{ displayName }}</span></div>
    <nav class="project-steps" aria-label="项目工作流程"><router-link v-for="step in steps" :key="step.key" :to="`/project/${projectId}${step.suffix}`" class="project-step" :class="{ active: currentTab === step.key }" :aria-current="currentTab === step.key ? 'step' : undefined"><span class="step-number">{{ step.number }}</span><span>{{ step.label }}</span><span class="step-arrow" aria-hidden="true">›</span></router-link></nav>
    <p class="step-hint"><span>这一步</span>{{ hints[currentTab] }}</p>
  </div>
</template>

<style scoped>
.project-header-nav { margin-bottom: 32px; }.project-breadcrumb { display: flex; align-items: center; gap: 12px; font-size: 12px; color: #a1a1a6; padding: 0 0 22px; }.project-breadcrumb a { color: #6e6e73; text-decoration: none; white-space: nowrap; }.project-breadcrumb a:hover { color: #0066cc; }.project-name { color: #1d1d1f; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.project-steps { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); border: 1px solid #e5e5e9; border-radius: 15px; padding: 6px; background: #fff; gap: 5px; }.project-step { display: flex; align-items: center; gap: 12px; padding: 16px; border-radius: 10px; color: #86868b; text-decoration: none; font-size: 12px; transition: background .2s,color .2s; }.project-step:hover { background: #f5f5f7; color: #1d1d1f; }.project-step.active { color: #0066cc; background: #edf4ff; }.step-number { font-size: 10px; font-variant-numeric: tabular-nums; opacity: .75; }.step-arrow { margin-left: auto; color: #d0d0d5; font-size: 17px; }.step-hint { color: #6e6e73; font-size: 12px; line-height: 1.8; margin: 16px 0 0; }.step-hint>span { color: #1d1d1f; font-weight: 550; margin-right: 12px; }
@media(max-width: 800px) { .project-step { padding: 13px 10px; gap: 7px; }.step-arrow { display: none; } }
@media(max-width: 500px) { .project-steps { grid-template-columns: 1fr 1fr; }.project-step { padding: 12px; }.step-hint { font-size: 11px; }.project-breadcrumb { padding-bottom: 18px; }.project-header-nav { margin-bottom: 24px; } }
</style>
