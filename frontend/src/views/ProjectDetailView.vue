<template>
  <div class="project-detail">
    <!-- Apple-style Sub-navigation Bar -->
    <ProjectHeaderNav :project-id="id" current-tab="overview" :project-name="project?.name" />

    <div v-if="loading" ><el-skeleton :rows="6" animated /></div>
    <template v-else-if="project">
      <!-- 项目头部 -->
      <div class="project-header card mb-24">
        <div class="flex-between">
          <div>
            <div class="project-title">{{ project.name }}</div>
            <div class="project-sub">
              <el-tag v-if="project.domain" type="info" size="small">{{ project.domain }}</el-tag>
              <el-tag v-if="project.article_type" size="small" type="success">{{ project.article_type }}</el-tag>
              <el-tag v-if="project.translation_model" size="small">{{ project.translation_model }}</el-tag>
            </div>
          </div>
          <div class="flex gap-8">
            <el-button @click="$router.push(`/project/${id}/terminology`)">
              <el-icon><Search /></el-icon> 术语查证
            </el-button>
            <el-button type="primary" @click="$router.push(`/project/${id}/translate`)">
              <el-icon><EditPen /></el-icon> 翻译工作台
            </el-button>
            <el-button type="warning" @click="$router.push(`/project/${id}/proofread`)">
              <el-icon><Checked /></el-icon> 校对报告
            </el-button>
            <el-button type="danger" plain @click="handleDeleteProject">
              <el-icon><Delete /></el-icon> 删除项目
            </el-button>
          </div>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stat-grid mb-24">
        <div class="stat-card">
          <div class="stat-label">总段落数</div>
          <div class="stat-value">{{ stats?.segments?.total || 0 }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">已翻译</div>
          <div class="stat-value">{{ stats?.segments?.translated || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已审定</div>
          <div class="stat-value">{{ stats?.segments?.approved || 0 }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">待处理</div>
          <div class="stat-value">{{ stats?.segments?.pending || 0 }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">FLAG 标记</div>
          <div class="stat-value">{{ stats?.segments?.flagged || 0 }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">待裁决问题</div>
          <div class="stat-value">{{ stats?.issues?.by_status?.pending || 0 }}</div>
        </div>
      </div>

      <!-- 进度 -->
      <div class="card mb-24">
        <div class="flex-between mb-16">
          <strong>翻译进度</strong>
          <span style="color: #888">{{ stats?.progress_percent || 0 }}%</span>
        </div>
        <el-progress :percentage="stats?.progress_percent || 0" :stroke-width="16" :format="() => ''" />
      </div>

      <!-- 上传文档区域 -->
      <div class="card mb-24">
        <div class="flex-between mb-16">
          <strong>📎 上传论文文档</strong>
          <span class="text-secondary" style="font-size: 13px;">支持 PDF、DOCX、TXT</span>
        </div>

        <el-upload
          drag
          :action="`http://127.0.0.1:8000/api/v1/documents/upload/${id}`"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          :show-file-list="true"
          accept=".pdf,.docx,.doc,.txt"
        >
          <el-icon class="el-icon--upload" size="48"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖放文件到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">上传后自动解析段落，生成编号 S001、S002...</div>
          </template>
        </el-upload>

        <!-- 已上传文档列表 -->
        <div v-if="documents.length > 0" class="uploaded-docs mt-16">
          <el-table :data="documents" size="small">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="file_type" label="类型" width="80" />
            <el-table-column label="解析状态" width="100">
              <template #default="{ row }">
                <el-tag :type="parseStatusType(row.parse_status)" size="small">
                  {{ parseStatusLabel(row.parse_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="word_count" label="字数" width="80" />
            <el-table-column prop="segment_count" label="段落数" width="80" />
          </el-table>
        </div>
      </div>

      <!-- 期刊选择 -->
      <div class="card mb-24">
        <div class="flex-between mb-16">
          <div>
            <strong style="font-size: 16px;">🎯 选择目标投稿期刊（注入风格规范）</strong>
            <div style="font-size: 13px; color: #888; margin-top: 4px;">
              选择后，期刊的英美拼写规范、篇幅限制与时态要求将直接作为硬性约束注入翻译大模型提示词中
            </div>
          </div>
          <router-link to="/journals" style="font-size: 13px; color: #4096ff; text-decoration: none;">
            管理期刊库 ↗
          </router-link>
        </div>

        <div>
          <el-select
            v-model="selectedJournalId"
            placeholder="点击直接展开下拉列表滚动查找，或输入期刊名称/缩写快速筛选..."
            filterable
            clearable
            size="large"
            style="width: 100%"
            @change="applyJournal"
            :loading="journalLoading"
          >
            <el-option
              v-for="j in journalOptions"
              :key="j.id"
              :label="`${j.name}${j.abbreviation ? ' (' + j.abbreviation + ')' : ''}`"
              :value="j.id"
            >
              <div class="journal-option-row">
                <div class="journal-option-title">
                  <span class="j-name">{{ j.name }}</span>
                  <span class="j-abbr" v-if="j.abbreviation">[{{ j.abbreviation }}]</span>
                </div>
                <div class="journal-option-tags">
                  <el-tag size="small" type="info">{{ j.domain }}</el-tag>
                  <el-tag size="small" :type="j.english_variant === 'British' ? 'warning' : 'success'">
                    {{ j.english_variant }} English
                  </el-tag>
                  <el-tag size="small" type="danger" v-if="j.impact_factor">IF {{ j.impact_factor }}</el-tag>
                </div>
              </div>
            </el-option>
          </el-select>

          <!-- 选中期刊的详细规范卡片 -->
          <div v-if="currentJournal" class="journal-detail mt-16">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="出版商">{{ currentJournal.publisher }}</el-descriptions-item>
              <el-descriptions-item label="学科领域">{{ currentJournal.domain }}</el-descriptions-item>
              <el-descriptions-item label="英语规范">
                <el-tag size="small" :type="currentJournal.english_variant === 'British' ? 'warning' : 'success'">
                  {{ currentJournal.english_variant }} English
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="引用格式">{{ currentJournal.citation_style }}</el-descriptions-item>
              <el-descriptions-item label="摘要字数上限">{{ currentJournal.abstract_word_limit ? currentJournal.abstract_word_limit + ' 词' : '未设定' }}</el-descriptions-item>
              <el-descriptions-item label="官方指南 URL">
                <a v-if="currentJournal.author_guide_url" :href="currentJournal.author_guide_url" target="_blank" style="color: #4096ff;">
                  查看官方投稿指南 ↗
                </a>
                <span v-else style="color: #aaa">未录入</span>
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="currentJournal.style_rules" class="style-rules-box mt-8">
              <div style="font-size: 12px; font-weight: 600; color: #555; margin-bottom: 4px;">
                📋 已加载的官方指南风格约束（将注入模型输入）：
              </div>
              <ul style="font-size: 12px; color: #666; padding-left: 20px; line-height: 1.8;">
                <li v-if="currentJournal.style_rules.tense"><strong>时态规范：</strong>{{ currentJournal.style_rules.tense }}</li>
                <li v-if="currentJournal.style_rules.voice"><strong>语态规范：</strong>{{ currentJournal.style_rules.voice }}</li>
                <li v-if="currentJournal.style_rules.abbreviations"><strong>缩写规范：</strong>{{ currentJournal.style_rules.abbreviations }}</li>
                <li v-for="(rule, idx) in (currentJournal.style_rules.other || [])" :key="idx">
                  <strong>附加要求：</strong>{{ rule }}
                </li>
              </ul>
            </div>

            <el-alert
              type="success"
              :closable="false"
              class="mt-8"
              title="期刊语言风格与硬性约束已生效：后续翻译与校对将严格依照该期刊指南执行"
              show-icon
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, EditPen, Checked, UploadFilled, Delete } from '@element-plus/icons-vue'
import ProjectHeaderNav from '../components/ProjectHeaderNav.vue'
import { projectsApi, documentsApi, journalsApi } from '../api'

const route = useRoute()
const router = useRouter()
const id = computed(() => Number(route.params.id))
const project = ref<any>(null)
const stats = ref<any>(null)
const documents = ref<any[]>([])
const loading = ref(false)
const selectedJournalId = ref<number | null>(null)
const currentJournal = ref<any>(null)
const journalOptions = ref<any[]>([])
const journalLoading = ref(false)

const handleDeleteProject = async () => {
  if (!project.value) return
  await ElMessageBox.confirm(
    `确定要删除项目「${project.value.name}」吗？包含的所有文档、段落和记录将被彻底清除，此操作不可撤销。`,
    '删除确认',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
  )
  try {
    await projectsApi.delete(id.value)
    ElMessage.success('项目已成功删除')
    router.push('/')
  } catch (e: any) {
    ElMessage.error('删除失败: ' + e.message)
  }
}

const parseStatusType = (s: string) => ({ pending: 'info', parsing: 'warning', done: 'success', error: 'danger' }[s] || 'info')
const parseStatusLabel = (s: string) => ({ pending: '等待中', parsing: '解析中', done: '已完成', error: '解析错误' }[s] || s)

const loadProject = async () => {
  loading.value = true
  try {
    const [p, s, docs] = await Promise.all([
      projectsApi.get(id.value),
      projectsApi.stats(id.value),
      documentsApi.listByProject(id.value),
    ]) as any[]
    project.value = p
    stats.value = s
    documents.value = docs
    if (p.journal_id) {
      selectedJournalId.value = p.journal_id
      currentJournal.value = await journalsApi.get(p.journal_id)
    }
  } catch (e: any) {
    ElMessage.error('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

const loadAllJournals = async () => {
  journalLoading.value = true
  try {
    journalOptions.value = await journalsApi.list({ limit: 100 }) as any[]
  } catch (e) {
    console.error('加载期刊列表失败', e)
  } finally {
    journalLoading.value = false
  }
}

const applyJournal = async (journalId: number | null) => {
  try {
    await projectsApi.update(id.value, { journal_id: journalId })
    if (journalId) {
      currentJournal.value = journalOptions.value.find(j => j.id === journalId) || await journalsApi.get(journalId)
      ElMessage.success(`目标期刊「${currentJournal.value?.name}」语言规范已注入`)
    } else {
      currentJournal.value = null
      ElMessage.info('已清除目标期刊设定')
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const beforeUpload = (file: File) => {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'docx', 'doc', 'txt'].includes(ext || '')) {
    ElMessage.error('仅支持 PDF、DOCX、TXT 格式')
    return false
  }
  return true
}

const handleUploadSuccess = () => {
  ElMessage.success('文件上传成功，正在后台解析...')
  setTimeout(() => loadProject(), 2000)
}

const handleUploadError = () => {
  ElMessage.error('文件上传失败，请检查后端服务是否运行')
}

onMounted(() => {
  loadProject()
  loadAllJournals()
})
</script>

<style scoped>
.project-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.project-sub {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mt-8 { margin-top: 8px; }
.mt-16 { margin-top: 16px; }
.text-secondary { color: #888; }

.uploaded-docs {
  border-top: 1px solid #f0f4f8;
  padding-top: 16px;
}

.journal-option-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
  gap: 16px;
}

.journal-option-title {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.j-name {
  font-weight: 600;
  color: #1a1a2e;
}

.j-abbr {
  font-size: 12px;
  color: #888;
}

.journal-option-tags {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
}

.style-rules-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 14px;
}
</style>
