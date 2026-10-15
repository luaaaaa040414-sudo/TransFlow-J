<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSourceTiers, classifySource } from '../api/modules'

const tiers = ref({})
const loading = ref(true)
const urlInput = ref('')
const verdict = ref(null)

const load = async () => {
  loading.value = true
  try {
    tiers.value = (await fetchSourceTiers())?.data || {}
  } finally {
    loading.value = false
  }
}

const check = async () => {
  if (!urlInput.value.trim()) return
  verdict.value = (await classifySource(urlInput.value))?.data || null
}

const tagType = (tier) => (tier === 'tier1' ? 'success' : tier === 'tier2' ? 'warning' : 'danger')

onMounted(load)
</script>

<template>
  <div class="sources">
    <el-card shadow="never">
      <template #header><span class="card-title">信源分级体系</span></template>
      <el-alert type="info" :closable="false" show-icon
        title="一级源可直接定译；二级源需两个独立来源交叉一致；三级源（黑名单）一律禁止" />

      <div class="check-row">
        <el-input v-model="urlInput" placeholder="粘贴信源链接，判定其等级，例如 https://termonline.cn/..." />
        <el-button type="primary" @click="check">判定</el-button>
      </div>

      <div v-if="verdict" class="verdict">
        <el-tag :type="tagType(verdict.tier)" size="large">
          {{ verdict.tierLabel || verdict.tier }}
        </el-tag>
        <span class="verdict__reason">{{ verdict.reason }}</span>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <template #header><span class="card-title">分级清单</span></template>
      <div v-for="(group, key) in tiers" :key="key" class="tier-group">
        <div class="tier-group__head">
          <el-tag :type="tagType(key)">{{ group.label }}</el-tag>
          <span class="tier-group__rule">{{ group.rule }}</span>
        </div>
        <el-table :data="group.sources" size="small" border stripe>
          <el-table-column prop="id" label="编号" width="80" />
          <el-table-column prop="name" label="信源" min-width="200" />
          <el-table-column prop="affiliation" label="归属" width="120" />
          <el-table-column prop="hits" label="引用次数" width="90" />
          <el-table-column label="匹配域名">
            <template #default="{ row }">{{ (row.domains || []).join(', ') }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.card-title { font-weight: 500; }
.sources { display: flex; flex-direction: column; gap: 16px; }
.check-row { display: flex; gap: 12px; margin: 16px 0; }
.verdict { display: flex; align-items: center; gap: 12px; }
.verdict__reason { color: var(--el-text-color-secondary); font-size: 13px; }
.tier-group { margin-bottom: 24px; }
.tier-group__head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.tier-group__rule { font-size: 13px; color: var(--el-text-color-regular); }
</style>
