<template>
  <div class="workspace-view">
    <!-- Header -->
    <div class="page-header flex-between mb-32">
      <div>
        <div class="header-badge">WORKSPACE</div>
        <h1 class="page-title">你的翻译工作空间。</h1>
        <p class="page-desc">从一篇中文文稿开始，清楚地推进每一次翻译。</p>
      </div>
      <button class="apple-btn-primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        <span>新建项目</span>
      </button>
    </div>

    <div class="workspace-guide"><div><span class="guide-kicker">第一次使用？</span><h2>先创建项目，再上传文稿。</h2><p>随后按「原文与要求 → 术语查证 → 逐段翻译 → 校对与报告」推进。</p></div><span class="guide-symbol" aria-hidden="true">文<span>EN</span></span></div>

    <!-- Quick Stats Overview -->
    <div class="stat-grid mb-32">
      <div class="stat-card">
        <div class="stat-label">全部项目</div>
        <div class="stat-value">{{ projects.length }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">已完成项目</div>
        <div class="stat-value">{{ completedCount }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">翻译与校对中</div>
        <div class="stat-value">{{ activeCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">原文总段落</div>
        <div class="stat-value">{{ totalSegments }}</div>
      </div>
    </div>

    <div v-if="projects.length" class="project-list-toolbar"><h2>我的项目 <span>{{ projects.length }}</span></h2><el-input v-model="searchQuery" placeholder="查找项目名称或学科" clearable aria-label="查找项目" class="project-search"><template #prefix><el-icon><Search /></el-icon></template></el-input></div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="py-8">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- Empty state -->
    <div v-else-if="projects.length === 0" class="empty-apple-card">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#86868b" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <line x1="9" y1="15" x2="15" y2="15"></line>
        </svg>
      </div>
      <div class="empty-title">你的第一篇译稿，从这里开始。</div>
      <p class="empty-desc">先为文稿创建一个项目，再上传中文文件。术语、译文与校对记录会保存在同一个项目中。</p>
      <button class="apple-btn-primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建第一个项目
      </button>
    </div>

    <!-- Projects Grid -->
    <div v-else class="apple-projects-grid">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="apple-project-card"
        tabindex="0"
        :aria-label="`打开项目：${project.name}`"
        @keydown.enter.self="openProject(project.id)"
        @keydown.space.prevent.self="openProject(project.id)"
        @click="openProject(project.id)"
      >
        <!-- Card Header -->
        <div class="card-header-row">
          <div class="flex gap-8" style="align-items: center;">
            <span :class="`status-badge status-${project.status}`">
              {{ statusLabel(project.status) }}
            </span>
            <span v-if="project.article_type" class="article-type-tag">
              {{ project.article_type }}
            </span>
          </div>
          <button
            class="card-delete-btn"
            title="删除此项目"
            @click.stop="deleteProject(project)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>

        <!-- Project Title & Domain -->
        <h3 class="card-project-title" :title="project.name">
          {{ project.name }}
        </h3>
        <p class="card-project-domain">
          {{ project.domain || '通用学术领域' }}
        </p>

        <!-- Progress Row -->
        <div class="card-progress-wrap">
          <div class="progress-labels">
            <span class="label-text">译文覆盖进度</span>
            <span class="label-val">{{ project.translated_segments || 0 }} / {{ project.total_segments || 0 }} 句段</span>
          </div>
          <div class="apple-progress-bar">
            <div
              class="progress-fill"
              :style="{ width: `${progress(project)}%` }"
              :class="{ completed: progress(project) === 100 }"
            ></div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="card-footer-row">
          <div class="footer-meta">
            <span class="model-pill">{{ project.translation_model || '尚未选择模型' }}</span>
            <span class="date-text">{{ formatDate(project.updated_at) }}</span>
          </div>
          <div class="enter-pill">
            <span>打开项目</span>
            <span class="arrow">↗</span>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && projects.length && !filteredProjects.length" description="没有找到匹配的项目"><el-button @click="searchQuery = ''">清除搜索</el-button></el-empty>

    <!-- Create Project Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建学术翻译项目"
      width="min(600px, calc(100vw - 32px))"
      class="apple-dialog"
    >
      <p class="create-dialog-intro">先给文稿起个名字。创建后即可上传原文，模型和翻译要求可以随后设置。</p>
      <el-form :model="createForm" label-width="100px" :rules="createRules" ref="createFormRef">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="createForm.name" placeholder="例如：传感器性能研究 · 中译英" />
        </el-form-item>
        <el-form-item label="学科领域" prop="domain">
          <el-input v-model="createForm.domain" placeholder="如：石油与天然气工程 / 计算机视觉 / 医学" />
        </el-form-item>
        <el-collapse class="create-options"><el-collapse-item title="更多设置（文章类型、翻译模型与背景）" name="options">
        <el-form-item label="文章类型">
          <el-select v-model="createForm.article_type" style="width: 100%">
            <el-option label="研究论文（Research Article）" value="Research Article" />
            <el-option label="综述论文（Review Article）" value="Review Article" />
            <el-option label="短文（Short Communication）" value="Short Communication" />
            <el-option label="展览讲解稿（Museum Docent Script）" value="展览讲解稿 (Museum Docent Script)" />
            <el-option label="技术报告（Technical Report）" value="Technical Report" />
          </el-select>
        </el-form-item>
        <el-form-item label="翻译引擎">
          <div class="flex gap-8" style="width: 100%;">
            <el-select v-model="createForm.translation_provider" style="width: 180px">
              <el-option label="DeepSeek (推荐/高性价比)" value="deepseek" />
              <el-option label="学术仿真演示 (免Key)" value="simulation" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="Anthropic Claude" value="anthropic" />
              <el-option label="自定义兼容接口" value="custom" />
            </el-select>
            <el-input
              v-model="createForm.translation_model"
              placeholder="模型 ID，如 deepseek-chat"
              style="flex: 1"
            />
          </div>
        </el-form-item>
        <el-form-item label="背景简要">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选：输入项目背景、读者对象或翻译重难点约束（将自动注入翻译纲要 brief.md）"
          />
        </el-form-item>
        </el-collapse-item></el-collapse>
      </el-form>

      <template #footer>
        <div class="dialog-footer-row">
          <button class="apple-btn-secondary" @click="showCreateDialog = false">取消</button>
          <button class="apple-btn-primary" @click="createProject" :disabled="creating">
            {{ creating ? '创建并解析中...' : '立即创建项目' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search } from '@element-plus/icons-vue'
import { projectsApi } from '../api'

const router = useRouter()
const route = useRoute()
const projects = ref<any[]>([])
const searchQuery = ref('')
const filteredProjects = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return projects.value.filter(project => !query || `${project.name || ''} ${project.domain || ''}`.toLowerCase().includes(query))
})
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref()

const createForm = ref({
  name: '',
  domain: '',
  article_type: 'Research Article',
  translation_provider: 'deepseek',
  translation_model: 'deepseek-chat',
  description: '',
})

watch(() => createForm.value.translation_provider, (p) => {
  if (p === 'deepseek') createForm.value.translation_model = 'deepseek-chat'
  else if (p === 'simulation') createForm.value.translation_model = 'academic-simulation'
  else if (p === 'openai') createForm.value.translation_model = 'gpt-4o'
  else if (p === 'anthropic') createForm.value.translation_model = 'claude-3-5-sonnet-20241022'
})

const createRules = {
  name: [{ required: true, message: '请填写项目名称', trigger: 'blur' }],
}

const completedCount = computed(() => {
  return projects.value.filter(p => p.status === 'completed' || (p.total_segments > 0 && p.approved_segments === p.total_segments)).length
})

const activeCount = computed(() => {
  return projects.value.filter(p => p.status === 'translating' || p.status === 'translated' || p.status === 'reviewing' || p.status === 'proofreading').length
})

const totalSegments = computed(() => {
  return projects.value.reduce((acc, p) => acc + (p.total_segments || 0), 0)
})

const statusLabel = (status: string) => ({
  created: '未开始',
  parsing: '解析中',
  parsed: '已解析',
  translating: '翻译中',
  translated: '已翻译',
  reviewing: '校对中',
  proofreading: '校对中',
  approved: '已审定',
  completed: '已完成',
}[status] || status)

const progress = (p: any) => {
  if (!p.total_segments) return 0
  return Math.min(100, Math.round((p.translated_segments / p.total_segments) * 100))
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const loadProjects = async () => {
  loading.value = true
  try {
    projects.value = await projectsApi.list() as any[]
  } catch (e: any) {
    ElMessage.error('加载项目列表失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  await createFormRef.value?.validate()
  creating.value = true
  try {
    const project = await projectsApi.create(createForm.value) as any
    ElMessage.success('项目创建成功！')
    showCreateDialog.value = false
    projects.value.unshift(project)
    router.push(`/project/${project.id}`)
  } catch (e: any) {
    ElMessage.error('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}

const openProject = (id: number) => {
  router.push(`/project/${id}`)
}

const deleteProject = async (project: any) => {
  await ElMessageBox.confirm(
    `确定要删除项目「${project.name}」吗？包含的所有文档与段落将永久清除。`,
    '删除确认',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
  )
  try {
    await projectsApi.delete(project.id)
    projects.value = projects.value.filter(p => p.id !== project.id)
    ElMessage.success('项目已删除')
  } catch (e: any) {
    ElMessage.error('删除失败: ' + e.message)
  }
}

watch(() => route.query.create, (value) => {
  if (value === '1') showCreateDialog.value = true
}, { immediate: true })
watch(showCreateDialog, (visible) => {
  if (!visible && route.query.create) {
    const { create, ...query } = route.query
    router.replace({ path: route.path, query })
  }
})
onMounted(loadProjects)
</script>

<style scoped>
.workspace-view {
  max-width: 1360px;
  margin: 0 auto;
}

.header-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #0071e3;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.apple-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.28);
  font-family: inherit;
}

.apple-btn-primary:hover {
  background-color: #0077ed;
  transform: scale(1.02);
}

.apple-btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #ffffff;
  color: #1d1d1f;
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-size: 14px;
  font-weight: 500;
  padding: 10px 20px;
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
}

.apple-projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 22px;
}

.apple-project-card {
  background: #ffffff;
  border-radius: 22px;
  border: 1px solid rgba(0, 0, 0, 0.07);
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
  padding: 24px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  min-height: 230px;
}

.apple-project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 113, 227, 0.3);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.article-type-tag {
  font-size: 11px;
  font-weight: 500;
  color: #6e6e73;
  background: #f0f0f2;
  padding: 3px 8px;
  border-radius: 980px;
}

.card-delete-btn {
  background: transparent;
  border: none;
  color: #86868b;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.card-delete-btn:hover {
  background: #fff1f0;
  color: #ff3b30;
}

.card-project-title {
  font-size: 18px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 6px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-project-domain {
  font-size: 13px;
  color: #86868b;
  margin: 0 0 18px;
}

.card-progress-wrap {
  margin-bottom: 20px;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
}
.label-text { color: #86868b; font-weight: 500; }
.label-val { color: #1d1d1f; font-weight: 600; }

.apple-progress-bar {
  width: 100%;
  height: 6px;
  background: #f0f0f2;
  border-radius: 980px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #0071e3;
  border-radius: 980px;
  transition: width 0.4s ease;
}

.progress-fill.completed {
  background: #34c759;
}

.card-footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-pill {
  font-size: 11px;
  font-weight: 600;
  color: #48484a;
  background: #f5f5f7;
  padding: 2px 7px;
  border-radius: 4px;
}

.date-text {
  font-size: 12px;
  color: #a1a1a6;
}

.enter-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #0071e3;
  transition: transform 0.2s ease;
}

.apple-project-card:hover .enter-pill {
  transform: translateX(2px);
}

.enter-pill .arrow {
  font-size: 14px;
}

.empty-apple-card {
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.07);
  padding: 60px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 600px;
  margin: 0 auto;
}

.empty-icon {
  width: 72px;
  height: 72px;
  background: #f5f5f7;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: #1d1d1f;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #86868b;
  max-width: 440px;
  margin: 0 0 24px;
  line-height: 1.5;
}

.dialog-footer-row {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .apple-projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style scoped>
.workspace-guide { display: flex; justify-content: space-between; align-items: center; gap: 24px; border-radius: 22px; background: #eaf1fb; padding: 32px 36px; margin-bottom: 32px; overflow: hidden; }.guide-kicker { color: #0066cc; font-size: 11px; }.workspace-guide h2 { font-size: 23px; letter-spacing: -.7px; font-weight: 550; margin: 10px 0; }.workspace-guide p { font-size: 12px; line-height: 1.8; color: #6e6e73; margin: 0; }.guide-symbol { display: flex; gap: 4px; align-items: center; font-size: 39px; color: #4d7bb5; font-weight: 400; letter-spacing: -2px; padding-right: 18px; }.guide-symbol span { display: inline-block; background: #fff; font: 22px Georgia; padding: 12px; border-radius: 10px; transform: rotate(8deg); box-shadow: 0 5px 15px #6783a524; margin-left: -7px; }.project-list-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin: 38px 0 20px; }.project-list-toolbar h2 { font-size: 22px; font-weight: 550; margin: 0; white-space: nowrap; letter-spacing: -.5px; }.project-list-toolbar h2 span { color: #a1a1a6; font-size: 14px; margin-left: 8px; font-weight: 400; }.project-search { max-width: 260px; }.apple-projects-grid { grid-template-columns: repeat(auto-fill,minmax(min(100%,320px),1fr)); gap: 20px; }.apple-project-card { min-height: 240px; padding: 26px; box-shadow: none; border-color: #e5e5e9; }.apple-project-card:hover { transform: translateY(-3px); border-color: #c8d5e8; box-shadow: 0 12px 35px -16px #53688630; }.card-project-title { font-size: 20px; font-weight: 550; line-height: 1.5; letter-spacing: -.5px; }.apple-btn-primary { font-weight: 500; box-shadow: none; padding: 12px 20px; }.apple-btn-primary:hover { transform: none; }.stat-grid { gap: 0; background: #fff; border: 1px solid #e5e5e9; border-radius: 18px; overflow: hidden; }.stat-card { border: none; border-radius: 0; box-shadow: none; padding: 24px 28px; background: transparent; position: relative; }.stat-card:not(:last-child)::after { content: ''; position: absolute; right: 0; top: 25%; height: 50%; width: 1px; background: #ededf0; }.stat-card:hover { transform: none; }.stat-card .stat-value { color: #1d1d1f; font-size: 31px; font-weight: 550; }.stat-label { font-size: 11px; margin-bottom: 12px; }.header-badge { color: #86868b; font-weight: 500; font-size: 10px; letter-spacing: .13em; margin-bottom: 16px; }.page-title { font-size: clamp(30px,3.5vw,42px); font-weight: 600; letter-spacing: -.045em; margin: 0 0 13px; }.page-desc { line-height: 1.8; font-size: 13px; }.create-dialog-intro { font-size: 12px; line-height: 1.8; margin: 0 0 24px; color: #6e6e73; }.empty-apple-card { max-width: none; border-style: dashed; box-shadow: none; padding: 58px 24px; }.empty-title { font-size: 23px; font-weight: 550; }.empty-desc { font-size: 13px; line-height: 1.9; }
@media(max-width: 700px) { .workspace-view>.page-header { align-items: flex-start; gap: 20px; flex-direction: column; }.workspace-guide { padding: 26px; }.workspace-guide h2 { font-size: 20px; }.guide-symbol { display: none; }.stat-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.stat-card { padding: 20px; }.stat-card:nth-child(2)::after { display: none; }.project-list-toolbar { flex-wrap: wrap; }.project-search { max-width: none; }.empty-title { font-size: 21px; } }
</style>

<style scoped>
.create-options { border-top: 1px solid #ededf0; border-bottom: 0; margin-top: 24px; }.create-options :deep(.el-collapse-item__header) { font-size: 12px; color: #6e6e73; font-weight: 400; background: transparent; }.create-options :deep(.el-collapse-item__wrap) { border: 0; }.create-options :deep(.el-collapse-item__content) { padding-top: 18px; padding-bottom: 0; }
</style>
