<template>
  <div class="translate-view">
    <!-- Apple-style Sub-navigation Bar -->
    <ProjectHeaderNav :project-id="id" current-tab="translate" />

    <!-- 工具栏 -->
    <div class="toolbar card mb-16">
      <div class="flex gap-8">
        <el-select v-model="provider" style="width: 195px">
          <el-option label="DeepSeek (推荐/已就绪)" value="deepseek" />
          <el-option label="学术仿真演示 (免Key)" value="simulation" />
          <el-option label="OpenAI (需配置Key)" value="openai" />
          <el-option label="Claude (需配置Key)" value="anthropic" />
          <el-option label="自定义兼容接口" value="custom" />
        </el-select>
        <el-input v-model="model" placeholder="模型 ID" style="width: 170px" />
        <el-button @click="testConnection" :loading="testingConn">
          <el-icon><Connection /></el-icon> 测试连接
        </el-button>
        <el-button link type="primary" @click="$router.push('/models')" style="font-size: 13px;">
          ⚙️ 配置Key
        </el-button>
        <el-divider direction="vertical" />
        <el-button type="primary" @click="translateAll" :loading="translatingAll">
          <el-icon><VideoPlay /></el-icon> 翻译全文
        </el-button>
        <el-button @click="translateSelected" :disabled="!selectedSegments.length" :loading="translatingSelected">
          翻译选中 ({{ selectedSegments.length }})
        </el-button>
      </div>
      <div class="flex gap-8">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 130px" @change="loadSegments">
          <el-option label="待翻译" value="pending" />
          <el-option label="已翻译" value="translated" />
          <el-option label="审定中" value="reviewing" />
          <el-option label="已审定" value="approved" />
          <el-option label="已标记" value="flagged" />
        </el-select>
        <el-select v-model="filterSection" placeholder="筛选章节" clearable style="width: 130px" @change="loadSegments">
          <el-option v-for="s in sections" :key="s" :label="s" :value="s" />
        </el-select>
      </div>
    </div>

    <!-- 段落列表 -->
    <div v-if="loadingSegs" class="card">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="segments.length === 0" class="card" style="text-align: center; padding: 40px;">
      <el-empty description="暂无段落，请先上传文档并等待解析完成" />
    </div>

    <div v-else class="segments-container">
      <div
        v-for="seg in segments"
        :key="seg.id"
        class="segment-card card"
        :class="{ 'is-flagged': seg.has_flag, 'is-selected': selectedSegments.includes(seg.id) }"
      >
        <!-- 段落头部 -->
        <div class="seg-header">
          <div class="flex gap-8" style="align-items: center;">
            <el-checkbox
              :model-value="selectedSegments.includes(seg.id)"
              @change="toggleSelect(seg.id)"
            />
            <span class="segment-id">{{ seg.segment_id }}</span>
            <span class="section-label">{{ seg.section }}</span>
            <span :class="`status-badge status-${seg.status}`">{{ statusLabel(seg.status) }}</span>
            <el-tag v-if="seg.has_flag" type="danger" size="small" effect="light">
              🚩 FLAG: {{ seg.flag_reason?.slice(0, 30) }}...
            </el-tag>
          </div>
          <div class="flex gap-8">
            <el-button
              size="small"
              type="primary"
              @click="translateSegment(seg)"
              :loading="translatingIds.includes(seg.id)"
              link
            >
              <el-icon><Refresh /></el-icon> 翻译
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="approveSegment(seg)"
              :disabled="!seg.translated_text"
              link
            >
              <el-icon><Check /></el-icon> 审定
            </el-button>
          </div>
        </div>

        <!-- 双栏对照 -->
        <div class="seg-body">
          <!-- 左：中文原文 -->
          <div class="seg-source">
            <div class="pane-label">中文原文</div>
            <div class="source-text">{{ seg.source_text }}</div>
          </div>
          <!-- 右：英文译文（可编辑） -->
          <div class="seg-target">
            <div class="pane-label">
              英文译文
              <span v-if="seg.numbers_issues?.length" class="number-warning">
                ⚠ {{ seg.numbers_issues.length }} 个数字问题
              </span>
              <span v-else-if="seg.translated_text && seg.numbers_verified" class="number-ok">✓ 数字一致</span>
            </div>
            <el-input
              v-model="editTexts[seg.id]"
              type="textarea"
              :rows="getRows(seg.source_text)"
              placeholder="等待翻译..."
              @blur="saveEdit(seg)"
              :class="{ 'has-flag': seg.has_flag }"
            />
            <!-- 数字问题提示 -->
            <div v-if="seg.numbers_issues?.length" class="number-issues">
              <div v-for="(issue, i) in seg.numbers_issues" :key="i" class="number-issue-item">
                ⚠ {{ issue.description }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="flex-between mt-16" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="loadSegments"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, VideoPlay, Refresh, Check } from '@element-plus/icons-vue'
import ProjectHeaderNav from '../components/ProjectHeaderNav.vue'
import { translationApi } from '../api'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const segments = ref<any[]>([])
const loadingSegs = ref(false)
const editTexts = ref<Record<number, string>>({})
const translatingIds = ref<number[]>([])
const translatingAll = ref(false)
const translatingSelected = ref(false)
const testingConn = ref(false)
const selectedSegments = ref<number[]>([])
const filterStatus = ref('')
const filterSection = ref('')
const currentPage = ref(1)
const pageSize = ref(30)
const total = ref(0)

const provider = ref('deepseek')
const model = ref('deepseek-chat')

watch(provider, (newP) => {
  if (newP === 'deepseek') model.value = 'deepseek-chat'
  else if (newP === 'simulation') model.value = 'academic-simulation'
  else if (newP === 'openai') model.value = 'gpt-4o'
  else if (newP === 'anthropic') model.value = 'claude-3-5-sonnet-20241022'
  else if (newP === 'custom') model.value = 'custom-model'
})

const sections = computed(() => {
  const s = new Set(segments.value.map(s => s.section).filter(Boolean))
  return Array.from(s)
})

const statusLabel = (status: string) => ({
  pending: '待翻译', translating: '翻译中', translated: '已翻译',
  reviewing: '审定中', approved: '已审定', flagged: '已标记'
}[status] || status)

const getRows = (text: string) => Math.max(3, Math.min(10, Math.ceil(text.length / 40)))

const loadSegments = async () => {
  loadingSegs.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterSection.value) params.section = filterSection.value

    const data = await translationApi.listSegments(id.value, params) as any[]
    segments.value = data
    // 初始化编辑文本
    data.forEach(seg => {
      editTexts.value[seg.id] = seg.translated_text || ''
    })
  } catch (e: any) {
    ElMessage.error('加载段落失败: ' + e.message)
  } finally {
    loadingSegs.value = false
  }
}

const translateSegment = async (seg: any) => {
  translatingIds.value.push(seg.id)
  try {
    const result = await translationApi.translateSegment(seg.id, provider.value, model.value) as any
    if (result.success) {
      seg.translated_text = result.segment.translated_text
      seg.has_flag = result.segment.has_flag
      seg.status = 'translated'
      seg.numbers_issues = result.segment.numbers_issues
      seg.numbers_verified = result.segment.numbers_verified
      editTexts.value[seg.id] = result.segment.translated_text
      ElMessage.success(`${seg.segment_id} 翻译完成`)
    }
  } catch (e: any) {
    ElMessage.error(`${seg.segment_id} 翻译失败: ` + e.message)
  } finally {
    translatingIds.value = translatingIds.value.filter(i => i !== seg.id)
  }
}

const translateAll = async () => {
  translatingAll.value = true
  try {
    await translationApi.translateProject(id.value, {
      provider: provider.value,
      model: model.value,
    })
    ElMessage.success('全文翻译任务已启动，请稍后刷新查看进度')
    setTimeout(loadSegments, 3000)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    translatingAll.value = false
  }
}

const translateSelected = async () => {
  if (!selectedSegments.value.length) return
  translatingSelected.value = true
  try {
    await translationApi.translateProject(id.value, {
      segment_ids: selectedSegments.value,
      provider: provider.value,
      model: model.value,
    })
    ElMessage.success(`已发送 ${selectedSegments.value.length} 个段落的翻译任务`)
    selectedSegments.value = []
    setTimeout(loadSegments, 3000)
  } finally {
    translatingSelected.value = false
  }
}

const saveEdit = async (seg: any) => {
  const newText = editTexts.value[seg.id]
  if (newText === seg.translated_text) return
  try {
    const updated = await translationApi.updateSegment(seg.id, { translated_text: newText }) as any
    seg.translated_text = updated.translated_text
    seg.numbers_issues = updated.numbers_issues
    seg.numbers_verified = updated.numbers_verified
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  }
}

const approveSegment = async (seg: any) => {
  try {
    await translationApi.updateSegment(seg.id, { status: 'approved', approved_text: editTexts.value[seg.id] })
    seg.status = 'approved'
    ElMessage.success(`${seg.segment_id} 已审定`)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const toggleSelect = (segId: number) => {
  const idx = selectedSegments.value.indexOf(segId)
  if (idx >= 0) selectedSegments.value.splice(idx, 1)
  else selectedSegments.value.push(segId)
}

const testConnection = async () => {
  testingConn.value = true
  try {
    const result = await translationApi.testConnection(provider.value, model.value) as any
    if (result.success) {
      ElMessage.success(`连接成功！模型响应：${result.response?.slice(0, 50)}`)
    } else {
      ElMessage.error(`连接失败：${result.error}`)
    }
  } finally {
    testingConn.value = false
  }
}

onMounted(loadSegments)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 20px;
}

.segments-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.segment-card {
  padding: 16px;
  transition: all 0.2s;
}

.segment-card.is-flagged {
  border-left: 3px solid #ff4d4f;
}

.segment-card.is-selected {
  border-left: 3px solid #4096ff;
  background: #f0f7ff;
}

.seg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.seg-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.pane-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.source-text {
  padding: 8px 12px;
  background: #f8fafb;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  border: 1px solid #eaeff4;
  min-height: 60px;
}

.number-warning { color: #faad14; font-size: 12px; }
.number-ok { color: #52c41a; font-size: 12px; }

.number-issues {
  margin-top: 6px;
}

.number-issue-item {
  font-size: 12px;
  color: #faad14;
  padding: 2px 0;
}

.mt-16 { margin-top: 16px; }
</style>
