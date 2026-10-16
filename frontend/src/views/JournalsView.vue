<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchDomains, fetchDomainDetail, fetchModels, styleTranslate } from '../api/modules'

const domains = ref([])
const active = ref(null)
const journals = ref([])
const journalCount = ref(0)
const loading = ref(false)
const selected = ref(null)

const models = ref([])
const modelId = ref('')
const scope = ref('paragraph')
const text = ref('')
const translating = ref(false)
const result = ref(null)

const load = async () => {
  try {
    domains.value = (await fetchDomains())?.data || []
  } catch (e) {
    ElMessage.error('领域列表加载失败，请确认后端已启动')
    return
  }
  if (domains.value.length && !active.value) {
    await select(domains.value[0].domain)
  }
}

const select = async (domain) => {
  active.value = domain
  selected.value = null
  result.value = null
  loading.value = true
  try {
    const detail = (await fetchDomainDetail(domain))?.data || {}
    journals.value = detail.journals || []
    journalCount.value = detail.journal_count ?? journals.value.length
    if (!journals.value.length) {
      ElMessage.warning('该领域下暂无已配置期刊')
    }
  } catch (e) {
    journals.value = []
    journalCount.value = 0
    ElMessage.error(`「${domain}」期刊列表加载失败：${e?.response?.status || ''} ${e?.message || ''}`)
  } finally {
    loading.value = false
  }
}

const pick = (row) => {
  selected.value = row
  result.value = null
}

const loadModels = async () => {
  const data = (await fetchModels())?.data || {}
  models.value = data.models || []
}

const doTranslate = async () => {
  if (!selected.value) {
    ElMessage.warning('请先在下方表格中点击选择一个目标期刊')
    return
  }
  if (!text.value.trim()) {
    ElMessage.warning('请输入要翻译的文本')
    return
  }
  translating.value = true
  try {
    result.value = (await styleTranslate({
      journal: selected.value.name,
      text: text.value,
      scope: scope.value,
      model: modelId.value || null
    }))?.data || null
  } finally {
    translating.value = false
  }
}

const oaTag = (v) => (v === true ? 'success' : v === 'hybrid' ? 'warning' : 'info')
const oaText = (v) => (v === true ? '开放获取' : v === 'hybrid' ? '混合' : '订阅')
const tierTag = (t) => (t === 'top' ? 'danger' : t === 'high' ? 'warning' : 'info')
const capStars = (n) => '★'.repeat(n) + '☆'.repeat(Math.max(0, 5 - n))

onMounted(() => {
  load()
  loadModels()
})
</script>

<template>
  <div class="journals">
    <el-card shadow="never">
      <template #header><span class="card-title">领域选择</span></template>
      <div class="domain-chips">
        <el-tag
          v-for="d in domains"
          :key="d.domain"
          :type="d.domain === active ? 'primary' : 'info'"
          effect="plain"
          size="large"
          class="domain-chip"
          @click="select(d.domain)"
        >
          {{ d.domain_zh }}
        </el-tag>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title">权威期刊列表</span>
        <el-tag v-if="journals.length" size="small" type="info" effect="plain" class="count-tag">
          共 {{ journalCount }} 本 · 点击某一行选定为翻译目标期刊
        </el-tag>
        <span v-else class="target-hint">点击某一行选定为翻译目标期刊</span>
      </template>
      <el-table v-loading="loading" :data="journals" size="small" border stripe highlight-current-row
        @row-click="pick" :current-row-key="selected?.name" row-key="name" empty-text="该领域暂无已配置期刊">
        <el-table-column prop="name" label="期刊" min-width="250" />
        <el-table-column prop="subfield" label="学科方向" width="150" show-overflow-tooltip />
        <el-table-column prop="publisher_zh" label="出版方" width="170" />
        <el-table-column label="影响力" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="tierTag(row.tier)">{{ row.tier }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开放获取" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="oaTag(row.open_access)">{{ oaText(row.open_access) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="语料采集范围" width="130">
          <template #default="{ row }">
            {{ row.collect_scope === 'fulltext' ? '可采集全文' : row.collect_scope === 'abstract_only' ? '仅公开摘要' : '仅元数据' }}
          </template>
        </el-table-column>
        <el-table-column prop="site" label="站点" min-width="210" />
        <el-table-column prop="note" label="备注" min-width="150" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title">
          期刊风格翻译
          <el-tag v-if="selected" size="small" type="primary" effect="dark" class="target-tag">
            目标期刊：{{ selected.name }}
          </el-tag>
          <span v-else class="target-hint">← 请先在上方表格选择一个期刊</span>
        </span>
      </template>

      <div class="trans-toolbar">
        <el-radio-group v-model="scope">
          <el-radio-button label="paragraph">成段翻译</el-radio-button>
          <el-radio-button label="full">整篇翻译</el-radio-button>
        </el-radio-group>

        <el-select v-model="modelId" placeholder="翻译模型（可选）" clearable style="width: 300px">
          <el-option v-for="m in models" :key="m.id" :label="`${m.name} · ${capStars(m.capability)} ${m.capability_label}`" :value="m.id" />
        </el-select>

        <el-button type="primary" :loading="translating" :disabled="!selected" @click="doTranslate">
          开始翻译
        </el-button>
      </div>

      <el-input v-model="text" type="textarea" :rows="8"
        placeholder="在此粘贴要翻译的源文本（成段翻译建议一段一贴；整篇翻译可粘贴全文）" />

      <div v-if="result" class="trans-result">
        <el-alert v-if="result.status !== 'ok' && result.status !== 'success'"
          :title="result.message || '模型未接入'" type="warning" :closable="false" show-icon />
        <div v-if="result.translation" class="trans-output">
          <div class="trans-output__label">译文</div>
          <pre>{{ result.translation }}</pre>
        </div>
        <el-descriptions v-if="result.style_card" title="风格约束卡" :column="2" border size="small" class="style-card">
          <el-descriptions-item label="期刊">{{ result.style_card.journal || '—' }}</el-descriptions-item>
          <el-descriptions-item label="领域">{{ result.style_card.domain_zh || '—' }}</el-descriptions-item>
          <el-descriptions-item label="语体">{{ result.style_card.register }}</el-descriptions-item>
          <el-descriptions-item label="人称">{{ result.style_card.person }}</el-descriptions-item>
          <el-descriptions-item label="术语">{{ result.style_card.terminology }}</el-descriptions-item>
          <el-descriptions-item label="句法">{{ result.style_card.sentence }}</el-descriptions-item>
          <el-descriptions-item label="数字单位">{{ result.style_card.numbers }}</el-descriptions-item>
          <el-descriptions-item label="引擎">{{ result.engine }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.card-title { font-weight: 500; }
.journals { display: flex; flex-direction: column; gap: 16px; }
.domain-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.domain-chip { cursor: pointer; }
.count-tag { margin-left: 8px; }
.target-tag { margin-left: 8px; }
.target-hint { margin-left: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
.trans-toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.trans-result { margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
.trans-output__label { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 6px; }
.trans-output pre { background: var(--el-fill-color-light); padding: 12px; border-radius: 8px; font-size: 13px; line-height: 1.7; white-space: pre-wrap; margin: 0; }
.style-card { margin-top: 4px; }
</style>
