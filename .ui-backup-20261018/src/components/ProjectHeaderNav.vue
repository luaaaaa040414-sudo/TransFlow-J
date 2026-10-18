<template>
  <div class="project-header-nav mb-20">
    <div class="nav-inner">
      <!-- Left: Back Button & Project Meta -->
      <div class="nav-left">
        <button class="apple-back-btn" @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>{{ backLabel }}</span>
        </button>
        <div class="divider"></div>
        <div class="project-info">
          <span class="project-badge">#{{ projectId }}</span>
          <span class="project-name" :title="displayName">{{ displayName }}</span>
        </div>
      </div>

      <!-- Right: Apple Segmented Pill Navigation -->
      <div class="nav-right">
        <div class="segmented-control">
          <button
            class="seg-item"
            :class="{ active: currentTab === 'overview' }"
            @click="$router.push(`/project/${projectId}`)"
          >
            <el-icon><Document /></el-icon>
            <span>概览</span>
          </button>
          <button
            class="seg-item"
            :class="{ active: currentTab === 'terminology' }"
            @click="$router.push(`/project/${projectId}/terminology`)"
          >
            <el-icon><Search /></el-icon>
            <span>术语查证</span>
          </button>
          <button
            class="seg-item"
            :class="{ active: currentTab === 'translate' }"
            @click="$router.push(`/project/${projectId}/translate`)"
          >
            <el-icon><EditPen /></el-icon>
            <span>翻译工作台</span>
          </button>
          <button
            class="seg-item"
            :class="{ active: currentTab === 'proofread' }"
            @click="$router.push(`/project/${projectId}/proofread`)"
          >
            <el-icon><Checked /></el-icon>
            <span>校对与报告</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Document, Search, EditPen, Checked } from '@element-plus/icons-vue'
import { projectsApi } from '../api'

const props = defineProps<{
  projectId: number | string
  currentTab: 'overview' | 'terminology' | 'translate' | 'proofread'
  projectName?: string
}>()

const router = useRouter()
const fetchedName = ref('')

const displayName = computed(() => {
  return props.projectName || fetchedName.value || `项目 #${props.projectId}`
})

const backLabel = computed(() => {
  if (props.currentTab === 'overview') return '返回工作台'
  return '返回概览'
})

const handleBack = () => {
  if (props.currentTab === 'overview') {
    router.push('/')
  } else {
    router.push(`/project/${props.projectId}`)
  }
}

onMounted(async () => {
  if (!props.projectName && props.projectId) {
    try {
      const res = await projectsApi.get(Number(props.projectId))
      if (res && res.name) {
        fetchedName.value = res.name
      }
    } catch (e) {
      // ignore
    }
  }
})
</script>

<style scoped>
.project-header-nav {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 18px;
  padding: 8px 16px;
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.apple-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f0f0f2;
  border: none;
  color: #1d1d1f;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  font-family: inherit;
}

.apple-back-btn:hover {
  background: #e4e4e7;
  transform: translateX(-1px);
}

.divider {
  width: 1px;
  height: 20px;
  background: rgba(0, 0, 0, 0.1);
}

.project-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-badge {
  font-size: 11px;
  font-weight: 700;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 2px 8px;
  border-radius: 980px;
  flex-shrink: 0;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 360px;
}

/* Apple Segmented Control */
.nav-right {
  display: flex;
  align-items: center;
}

.segmented-control {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f0f0f2;
  padding: 3px;
  border-radius: 980px;
}

.seg-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 980px;
  border: none;
  background: transparent;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  font-family: inherit;
}

.seg-item:hover {
  color: #1d1d1f;
}

.seg-item.active {
  background: #ffffff;
  color: #1d1d1f;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

@media (max-width: 768px) {
  .project-name {
    max-width: 160px;
  }
  .segmented-control {
    width: 100%;
    justify-content: space-between;
  }
  .seg-item span {
    font-size: 12px;
  }
}
</style>
