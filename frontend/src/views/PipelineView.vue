<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { runPipeline } from '../api/modules'

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
        <el-select v-model="direction" style="width: 160px">
          <el-option label="汉译英 zh → en" value="zh-en" />
          <el-option label="英译汉 en → zh" value="en-zh" />
        </el-select>
        <el-input v-model="journal" placeholder="目标期刊（留空则通用风格）" style="width: 260px" />
        <el-button type="primary" :loading="running" @click="start">开始翻译</el-button>
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
.pipeline__toolbar { display: flex; gap: 12px; margin-bottom: 12px; }
.pipeline__result pre { background: var(--el-fill-color-light); padding: 12px; border-radius: 8px; font-size: 12px; overflow: auto; max-height: 360px; }
</style>
