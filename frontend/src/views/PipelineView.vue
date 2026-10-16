<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { runPipeline, fetchAllJournals } from '../api/modules'

const stages = [
  { key: 'prep', label: '译前准备', desc: '术语抽取 · 信源核查 · 术语表锁定' },
  { key: 'translate', label: '翻译', desc: '模型 A 精准初译' },
  { key: 'review', label: '校对反思', desc: '模型 B 重译 · 模型 C 裁决' },
  { key: 'finalize', label: '定稿交付', desc: '风格校准 · 术语回溯 · 报告' }
]

const direction = ref('zh-en')
const journal = ref('')
const sourceText = ref('')
const running = ref(false)
const activeStage = ref('')
const jobResult = ref(null)

// 目标期刊只能从项目已配置、可实现风格的期刊里选，不允许自由输入
const journals = ref([])
const journalsLoading = ref(false)

const journalGroups = computed(() => {
  const map = new Map()
  for (const j of journals.value) {
    const key = j.domain_zh || j.domain || '其他'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(j)
  }
  return [...map.entries()].map(([label, options]) => ({ label, options }))
})

const loadJournals = async () => {
  journalsLoading.value = true
  try {
    journals.value = (await fetchAllJournals())?.data || []
  } finally {
    journalsLoading.value = false
  }
}

const start = async () => {
  if (!sourceText.value.trim()) {
    ElMessage.warning('请先输入源文本')
    return
  }
  running.value = true
  activeStage.value = 'prep'
  try {
    const res = await runPipeline({
      direction: direction.value,
      journal: journal.value || null,
      text: sourceText.value
    })
    jobResult.value = res?.data || null
    activeStage.value = 'finalize'
  } catch (e) {
    jobResult.value = null
  } finally {
    running.value = false
  }
}

onMounted(loadJournals)
</script>

<template>
  <div class="pipeline">
    <el-card shadow="never" class="pipeline__card">
      <el-steps :active="stages.findIndex((s) => s.key === activeStage) + 1" align-center finish-status="success">
        <el-step v-for="s in stages" :key="s.key" :title="s.label" :description="s.desc" />
      </el-steps>
    </el-card>

    <el-card shadow="never" class="pipeline__card">
      <div class="pipeline__toolbar">
        <el-select v-model="direction" style="width: 170px">
          <el-option label="汉译英 zh → en" value="zh-en" />
          <el-option label="英译汉 en → zh" value="en-zh" />
        </el-select>

        <el-select
          v-model="journal"
          filterable
          clearable
          :loading="journalsLoading"
          placeholder="目标期刊（留空则通用学术风格）"
          style="width: 380px"
        >
          <el-option-group v-for="g in journalGroups" :key="g.label" :label="g.label">
            <el-option
              v-for="j in g.options"
              :key="j.name"
              :label="j.name"
              :value="j.name"
            >
              <span class="opt-name">{{ j.name }}</span>
              <span class="opt-meta">
                <template v-if="j.subfield">{{ j.subfield }} · </template>{{ j.publisher_zh || '—' }}
              </span>
            </el-option>
          </el-option-group>
        </el-select>

        <el-button type="primary" :loading="running" @click="start">开始翻译</el-button>
      </div>

      <div class="pipeline__hint">
        期刊只能从已配置的 <b>{{ journals.length }}</b> 本权威期刊中选择 ——
        这些是项目已实现风格支持的刊；不在列表里的期刊暂时无法保证风格效果，因此不开放自由填写。
      </div>

      <el-input v-model="sourceText" type="textarea" :rows="10" placeholder="在此粘贴源文本，支持分段翻译" />
    </el-card>

    <el-card v-if="jobResult" shadow="never" class="pipeline__card">
      <template #header><span class="pipeline__card-title">译文与反思报告</span></template>
      <div class="pipeline__result">
        <pre>{{ JSON.stringify(jobResult, null, 2) }}</pre>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.pipeline { display: flex; flex-direction: column; gap: 16px; }
.pipeline__card-title { font-weight: 500; }
.pipeline__toolbar { display: flex; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
.pipeline__hint { font-size: 12px; color: var(--el-text-color-secondary); line-height: 1.7; margin-bottom: 12px; }
.pipeline__result pre { background: var(--el-fill-color-light); padding: 12px; border-radius: 8px; font-size: 12px; overflow: auto; max-height: 360px; }
.opt-name { margin-right: 12px; }
.opt-meta { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
