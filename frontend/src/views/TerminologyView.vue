<template>
  <div class="terminology-view">
    <!-- Apple-style Sub-navigation Bar -->
    <ProjectHeaderNav :project-id="id" current-tab="terminology" />

    <div class="page-header flex-between mb-24">
      <div>
        <div class="page-title">🔍 术语查证</div>
        <div class="page-desc">记录专业术语的权威信源证据，确认英文译法</div>
      </div>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加术语
      </el-button>
    </div>

    <!-- 统计 -->
    <div class="stat-grid mb-24">
      <div class="stat-card">
        <div class="stat-label">全部术语</div>
        <div class="stat-value">{{ terms.length }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">已确认</div>
        <div class="stat-value">{{ confirmedCount }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">待查证</div>
        <div class="stat-value">{{ pendingCount }}</div>
      </div>
    </div>

    <!-- 术语列表 -->
    <div class="card">
      <el-table :data="terms" v-loading="loading" stripe>
        <el-table-column prop="source_term" label="中文术语" width="160" />
        <el-table-column prop="domain" label="领域" width="120" />
        <el-table-column label="确认译法" width="200">
          <template #default="{ row }">
            <span v-if="row.confirmed_translation" class="confirmed-term">{{ row.confirmed_translation }}</span>
            <span v-else class="unconfirmed">未确认</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <div class="flex items-center gap-4">
              <el-tag :type="termStatusType(row.status)" size="small">
                {{ termStatusLabel(row.status) }}
              </el-tag>
              <el-tag v-if="row.decomposition && row.decomposition.length" type="warning" effect="plain" size="small">
                拆解推导
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="信源证据" width="100">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.evidence?.length || 0 }} 条</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="候选译法">
          <template #default="{ row }">
            <div class="flex gap-8 flex-wrap">
              <el-tag
                v-for="(t, i) in (row.candidate_translations || [])"
                :key="i"
                size="small"
                type="info"
                effect="plain"
              >{{ t }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="triggerAutoResearch(row)" link type="warning" :loading="researchingIds.includes(row.id)">逐级查证</el-button>
            <el-button size="small" @click="openDetail(row)" link type="primary">查看证据</el-button>
            <el-button size="small" @click="deleteTerm(row)" link type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加术语对话框 -->
    <el-dialog v-model="showAddDialog" title="添加术语" width="480px">
      <el-form :model="addForm" label-width="90px">
        <el-form-item label="中文术语" required>
          <el-input v-model="addForm.source_term" placeholder="输入专业术语" />
        </el-form-item>
        <el-form-item label="学科领域">
          <el-input v-model="addForm.domain" placeholder="如：石油工程 / 材料科学" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addTerm" :loading="adding">添加</el-button>
      </template>
    </el-dialog>

    <!-- 术语详情/证据对话框 -->
    <el-dialog v-model="showDetailDialog" :title="`权威查证与证据卡：${selectedTerm?.source_term}`" width="880px">
      <div v-if="selectedTerm">
        <!-- 4步查证流程流水线指示器 -->
        <div class="workflow-steps-banner mb-16">
          <div class="workflow-step" :class="{ 'active': true }">
            <div class="step-num">1</div>
            <div class="step-info">
              <div class="step-title">先查完整词语</div>
              <div class="step-desc">{{ selectedTerm.decomposition?.length ? '未命中单一词条' : '直接官方条目' }}</div>
            </div>
          </div>
          <div class="step-arrow">➔</div>
          <div class="workflow-step" :class="{ 'active': selectedTerm.decomposition?.length }">
            <div class="step-num">2</div>
            <div class="step-info">
              <div class="step-title">自动语义拆解</div>
              <div class="step-desc">核心专业术语 + 范围限定</div>
            </div>
          </div>
          <div class="step-arrow">➔</div>
          <div class="workflow-step" :class="{ 'active': true }">
            <div class="step-num">3</div>
            <div class="step-info">
              <div class="step-title">扩大权威信源</div>
              <div class="step-desc">1级官方 ➔ 2/3级行业期刊</div>
            </div>
          </div>
          <div class="step-arrow">➔</div>
          <div class="workflow-step" :class="{ 'active': true }">
            <div class="step-num">4</div>
            <div class="step-info">
              <div class="step-title">判断证据卡</div>
              <div class="step-desc">透明呈现与快速决断</div>
            </div>
          </div>
        </div>

        <!-- 语义拆解表（若属于复合词拆解） -->
        <div v-if="selectedTerm.decomposition && selectedTerm.decomposition.length" class="decomposition-box mb-16">
          <div class="box-title flex-between mb-8">
            <span class="font-bold">🧩 语义结构识别与拆解结果：</span>
            <el-tag size="small" type="warning" effect="plain">自动拆解分析</el-tag>
          </div>
          <table class="decomp-table">
            <thead>
              <tr>
                <th style="width: 140px;">组成部分</th>
                <th style="width: 160px;">识别作用</th>
                <th>查证依据与对应表达</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in selectedTerm.decomposition" :key="idx">
                <td class="font-bold text-primary">{{ p.part }}</td>
                <td>
                  <el-tag size="small" :type="p.role?.includes('核心') ? 'danger' : 'info'">
                    {{ p.role }}
                  </el-tag>
                </td>
                <td>
                  <span class="en-target font-bold">{{ p.en }}</span>
                  <span v-if="p.evidence" class="text-muted ml-8" style="font-size: 12px;">（{{ p.evidence }}）</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 权威判断证据卡 (Evidence Cards) -->
        <div class="cards-section mb-16">
          <div class="flex-between mb-12">
            <div>
              <strong style="font-size: 15px;">📋 权威判断证据卡 (Evidence Cards)</strong>
              <div class="text-muted" style="font-size: 12px; margin-top: 2px;">
                依据《翻译质量保障流程总表》信源优先级生成，提供推荐译法、适用领域、来源原文、链接与推荐理由
              </div>
            </div>
            <el-button
              size="small"
              type="warning"
              @click="triggerAutoResearch(selectedTerm)"
              :loading="researchingIds.includes(selectedTerm.id)"
            >
              🔄 重新查证
            </el-button>
          </div>

          <div v-if="selectedTerm.cards && selectedTerm.cards.length">
            <div
              v-for="(card, cIdx) in selectedTerm.cards"
              :key="cIdx"
              class="evidence-decision-card mb-16"
              :class="{ 'card-highlight': cIdx === 0 }"
            >
              <div class="card-top-bar flex-between">
                <div class="flex items-center gap-8">
                  <span class="card-badge">推荐 {{ Number(cIdx) + 1 }}</span>
                  <span class="card-title-en">{{ card.recommended_translation }}</span>
                  <el-tag size="small" :type="card.match_type === 'exact' ? 'success' : 'warning'">
                    {{ card.status_tag || (card.match_type === 'exact' ? '官方精确收录' : '组合推导译法') }}
                  </el-tag>
                </div>
                <el-button
                  type="success"
                  size="small"
                  @click="adoptCard(card.recommended_translation)"
                  :loading="confirming"
                >
                  <el-icon><Check /></el-icon> 确认采用此译法
                </el-button>
              </div>

              <div class="card-content">
                <div class="field-row">
                  <span class="field-k">🏷️ 适用领域：</span>
                  <span class="field-v font-bold">{{ card.domain || selectedTerm.domain || '通用学术' }}</span>
                </div>

                <!-- 推荐理由（特别声明核心术语与整体组合的区别） -->
                <div class="reason-banner" :class="card.match_type === 'exact' ? 'reason-exact' : 'reason-warning'">
                  <div class="reason-head">💡 推荐理由与证据说明：</div>
                  <div class="reason-body" style="white-space: pre-line;">{{ card.recommendation_reason }}</div>
                </div>

                <div class="field-row">
                  <span class="field-k">📖 来源原文：</span>
                  <div class="source-quote-box">
                    "{{ card.evidence_text }}"
                  </div>
                </div>

                <div class="field-row flex-between mt-8" style="align-items: center; gap: 8px;">
                  <div class="source-meta">
                    <span class="field-k">🏛️ 权威信源：</span>
                    <el-tag size="small" :type="levelTagType(card.source_level)">{{ card.source_level }}级信源</el-tag>
                    <span class="ml-8 text-secondary" style="font-size: 13px;">{{ card.source_name }}</span>
                  </div>
                  <a v-if="card.source_url" :href="card.source_url" target="_blank" class="source-external-link"
                     :title="isSearchUrl(card.source_url) ? '直接打开该信源针对本术语的检索结果页' : '该信源没有站内检索入口，打开官网后请手动检索'">
                    {{ sourceLinkText(card.source_url) }}
                  </a>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无判断证据卡，请点击右上角「重新查证」" :image-size="60" />
        </div>

        <!-- 确认译法快捷操作栏 -->
        <div class="card mb-16" style="background: #fafbfc;">
          <div class="flex-between">
            <strong>🎯 人工最终核定译法</strong>
            <div v-if="selectedTerm.confirmed_translation">
              <el-tag type="success">✓ 当前已确认：{{ selectedTerm.confirmed_translation }}</el-tag>
            </div>
            <div v-else>
              <el-tag type="warning">⏳ 待核定确认</el-tag>
            </div>
          </div>
          <div class="flex gap-8 mt-8">
            <el-select v-model="confirmTranslation" placeholder="从候选译法中选择或输入自定义译法" allow-create filterable style="flex:1">
              <el-option
                v-for="t in (selectedTerm.candidate_translations || [])"
                :key="t"
                :label="t"
                :value="t"
              />
            </el-select>
            <el-button type="primary" @click="doConfirm" :loading="confirming">
              <el-icon><Check /></el-icon> 确认采用
            </el-button>
          </div>
        </div>

        <!-- 原始信源证据明细表与手动添加 -->
        <el-collapse class="mb-16">
          <el-collapse-item title="📚 查看原始信源流水记录与手动添加证据" name="rawEvidence">
            <div class="flex-between mb-12">
              <span class="text-muted" style="font-size: 13px;">记录了系统自动检索和人工添加的所有原始信源片段</span>
              <el-button size="small" type="primary" plain @click="showEvidenceForm = !showEvidenceForm">
                + 手动添加证据
              </el-button>
            </div>

            <!-- 添加证据表单 -->
            <div v-if="showEvidenceForm" class="evidence-form mb-16">
              <el-form :model="evidenceForm" label-width="90px" size="small">
                <el-form-item label="信源等级">
                  <el-select v-model="evidenceForm.source_level" style="width:100%">
                    <el-option :value="1" label="1级 - 官方词典/标准机构" />
                    <el-option :value="2" label="2级 - 行业权威标准" />
                    <el-option :value="3" label="3级 - 权威专业期刊" />
                    <el-option :value="4" label="4级 - 知名媒体/教材" />
                    <el-option :value="5" label="5级 - 其他参考来源" />
                  </el-select>
                </el-form-item>
                <el-form-item label="来源类型">
                  <el-input v-model="evidenceForm.source_type" placeholder="官方词典 / 行业标准 / 专业期刊" />
                </el-form-item>
                <el-form-item label="来源名称">
                  <el-input v-model="evidenceForm.source_name" placeholder="如：TermOnline / Nature / ISO 标准" />
                </el-form-item>
                <el-form-item label="来源 URL">
                  <el-input v-model="evidenceForm.source_url" placeholder="实际可访问的页面 URL" />
                </el-form-item>
                <el-form-item label="候选译法">
                  <el-input v-model="evidenceForm.candidate_translation" placeholder="该信源支持的英文译法" />
                </el-form-item>
                <el-form-item label="证据原文">
                  <el-input v-model="evidenceForm.evidence_text" type="textarea" :rows="3"
                    placeholder="从原始页面提取的关键证据文字" />
                </el-form-item>
                <el-form-item label="发布日期">
                  <el-input v-model="evidenceForm.published_date" placeholder="如：2023-05 或 2023" />
                </el-form-item>
                <div class="flex gap-8" style="justify-content: flex-end">
                  <el-button @click="showEvidenceForm = false">取消</el-button>
                  <el-button type="primary" @click="submitEvidence" :loading="addingEvidence">保存证据</el-button>
                </div>
              </el-form>
            </div>

            <!-- 原始证据列表 -->
            <div v-if="selectedTerm.evidence?.length">
              <div
                v-for="ev in sortedEvidence"
                :key="ev.id"
                class="evidence-item"
                :class="{ 'invalid': !ev.is_valid }"
              >
                <div class="evidence-header">
                  <div class="flex gap-8" style="align-items: center;">
                    <el-tag :type="levelTagType(ev.source_level)" size="small">{{ ev.source_level }}级</el-tag>
                    <span class="evidence-source">{{ ev.source_name || ev.source_type }}</span>
                    <el-tag v-if="ev.candidate_translation" size="small" effect="plain" type="success">
                      {{ ev.candidate_translation }}
                    </el-tag>
                  </div>
                  <div class="flex gap-8">
                    <el-button size="small" link @click="verifyEvidence(ev, !ev.is_valid)">
                      {{ ev.is_valid ? '标记无效' : '标记有效' }}
                    </el-button>
                    <a v-if="ev.source_url" :href="ev.source_url" target="_blank"
                       style="font-size:12px; white-space:nowrap; flex-shrink:0;"
                       :title="isSearchUrl(ev.source_url) ? '直接打开该信源针对本术语的检索结果页' : '该信源没有站内检索入口，打开官网后请手动检索'">
                      {{ sourceLinkText(ev.source_url) }}
                    </a>
                  </div>
                </div>
                <div v-if="ev.evidence_text" class="evidence-text">
                  "{{ ev.evidence_text }}"
                </div>
                <div class="evidence-meta">
                  {{ ev.source_type }}
                  <span v-if="ev.published_date"> · {{ ev.published_date }}</span>
                  <span v-if="!ev.is_valid" style="color: #ff4d4f;"> · 已标记无效</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无原始信源记录" :image-size="50" />
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check } from '@element-plus/icons-vue'
import ProjectHeaderNav from '../components/ProjectHeaderNav.vue'
import { terminologyApi } from '../api'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const terms = ref<any[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const adding = ref(false)
const showDetailDialog = ref(false)
const selectedTerm = ref<any>(null)
const confirmTranslation = ref('')
const confirming = ref(false)
const showEvidenceForm = ref(false)
const addingEvidence = ref(false)

const confirmedCount = computed(() => terms.value.filter(t => t.status === 'confirmed').length)
const pendingCount = computed(() => terms.value.filter(t => t.status === 'pending').length)

const sortedEvidence = computed(() => {
  if (!selectedTerm.value?.evidence) return []
  return [...selectedTerm.value.evidence].sort((a, b) => a.source_level - b.source_level)
})

const addForm = ref({ source_term: '', domain: '', notes: '' })
const evidenceForm = ref({
  source_level: 1,
  source_type: '',
  source_name: '',
  source_url: '',
  candidate_translation: '',
  evidence_text: '',
  published_date: '',
})

const levelTagType = (level: number) => (['', 'danger', 'warning', 'success', 'info', ''][level] || 'info')

// 判断这个链接是不是「该站针对本术语的检索结果页」而不是网站首页。
// 后端已把首页地址改写成检索深链（source_links.py），但 DB 里的历史证据没有 kind 字段，
// 所以这里按 URL 形态兜底判断：带检索参数或检索路径的就算检索页。
const isSearchUrl = (url?: string) => {
  if (!url) return false
  return /[?&](q|qs|query|queryText|searchText|searchWord|searchword|keyword|term|AllField)=/i.test(url)
    || /\/(search|search-results|searchresult|doSearch)(\.|\/|\?|$)/i.test(url)
}
const sourceLinkText = (url?: string) => (isSearchUrl(url) ? '查看站内检索结果 ↗' : '打开信源官网 ↗')
const termStatusType = (s: string) => ((({ pending: 'info', confirmed: 'success', disputed: 'warning', rejected: 'danger' } as Record<string, any>)[s]) || 'info')
const termStatusLabel = (s: string) => ((({ pending: '待查证', confirmed: '已确认', disputed: '有争议', rejected: '已排除' } as Record<string, string>)[s]) || s)

const researchingIds = ref<number[]>([])

const triggerAutoResearch = async (term: any) => {
  researchingIds.value.push(term.id)
  try {
    const res = await terminologyApi.autoResearch(term.id) as any
    if (res.success && res.term) {
      const idx = terms.value.findIndex(t => t.id === term.id)
      if (idx >= 0) {
        terms.value[idx] = res.term
      }
      if (selectedTerm.value && selectedTerm.value.id === term.id) {
        selectedTerm.value = res.term
        confirmTranslation.value = res.term.confirmed_translation || (res.term.candidate_translations?.[0] || '')
      }
      const matchTag = res.term.decomposition?.length ? '（触发自动语义拆解并多级扩检）' : '（1级官方精确条目收录）'
      ElMessage.success(`术语「${term.source_term}」4步查证完毕${matchTag}，已生成证据卡`)
    }
  } catch (e: any) {
    ElMessage.error('自动查证失败: ' + e.message)
  } finally {
    researchingIds.value = researchingIds.value.filter(i => i !== term.id)
  }
}

const loadTerms = async () => {
  loading.value = true
  try {
    terms.value = await terminologyApi.list(id.value) as any[]
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

const addTerm = async () => {
  if (!addForm.value.source_term) {
    ElMessage.warning('请填写中文术语')
    return
  }
  adding.value = true
  try {
    const term = await terminologyApi.create(id.value, addForm.value) as any
    terms.value.unshift(term)
    showAddDialog.value = false
    addForm.value = { source_term: '', domain: '', notes: '' }
    ElMessage.success('术语已添加，正在执行自动查证...')
    // 自动触发4步查证
    triggerAutoResearch(term)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    adding.value = false
  }
}

const openDetail = async (term: any) => {
  selectedTerm.value = await terminologyApi.get(term.id) as any
  confirmTranslation.value = selectedTerm.value.confirmed_translation || (selectedTerm.value.candidate_translations?.[0] || '')
  showDetailDialog.value = true
  showEvidenceForm.value = false
}

const adoptCard = async (cand: string) => {
  confirmTranslation.value = cand
  await doConfirm()
}

const doConfirm = async () => {
  if (!confirmTranslation.value) {
    ElMessage.warning('请填写确认译法')
    return
  }
  confirming.value = true
  try {
    await terminologyApi.confirm(selectedTerm.value.id, confirmTranslation.value)
    selectedTerm.value.confirmed_translation = confirmTranslation.value
    selectedTerm.value.status = 'confirmed'
    // 更新列表
    const idx = terms.value.findIndex(t => t.id === selectedTerm.value.id)
    if (idx >= 0) {
      terms.value[idx].confirmed_translation = confirmTranslation.value
      terms.value[idx].status = 'confirmed'
    }
    ElMessage.success(`已确认：${selectedTerm.value.source_term} → ${confirmTranslation.value}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    confirming.value = false
  }
}

const submitEvidence = async () => {
  if (!evidenceForm.value.candidate_translation && !evidenceForm.value.evidence_text) {
    ElMessage.warning('请填写候选译法或证据原文')
    return
  }
  addingEvidence.value = true
  try {
    const ev = await terminologyApi.addEvidence(selectedTerm.value.id, evidenceForm.value) as any
    if (!selectedTerm.value.evidence) selectedTerm.value.evidence = []
    selectedTerm.value.evidence.push(ev)
    if (ev.candidate_translation) {
      if (!selectedTerm.value.candidate_translations) selectedTerm.value.candidate_translations = []
      if (!selectedTerm.value.candidate_translations.includes(ev.candidate_translation)) {
        selectedTerm.value.candidate_translations.push(ev.candidate_translation)
      }
    }
    showEvidenceForm.value = false
    evidenceForm.value = { source_level: 1, source_type: '', source_name: '', source_url: '', candidate_translation: '', evidence_text: '', published_date: '' }
    ElMessage.success('证据已保存')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    addingEvidence.value = false
  }
}

const verifyEvidence = async (ev: any, isValid: boolean) => {
  try {
    await terminologyApi.verifyEvidence(ev.id, isValid)
    ev.is_valid = isValid
    ElMessage.success(isValid ? '已标记有效' : '已标记无效')
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const deleteTerm = async (term: any) => {
  await ElMessageBox.confirm(`确定删除术语「${term.source_term}」？`, '确认', { type: 'warning' })
  try {
    await terminologyApi.delete(term.id)
    terms.value = terms.value.filter(t => t.id !== term.id)
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(loadTerms)
</script>

<style scoped>
.confirmed-term {
  color: #389e0d;
  font-weight: 600;
}

.unconfirmed {
  color: #aaa;
  font-style: italic;
}

.evidence-form {
  background: #f8fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e8edf3;
}

.evidence-item {
  padding: 12px;
  border: 1px solid #e8edf3;
  border-radius: 8px;
  margin-bottom: 10px;
  background: #fff;
}

.evidence-item.invalid {
  opacity: 0.6;
  background: #f5f5f5;
}

.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.evidence-source {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.evidence-text {
  font-size: 13px;
  color: #555;
  background: #f0f4f8;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 6px;
  font-style: italic;
  line-height: 1.6;
}

.evidence-meta {
  font-size: 12px;
  color: #aaa;
}

.mt-8 { margin-top: 8px; }
.flex-wrap { flex-wrap: wrap; }

/* 4步查证流水线指示器 */
.workflow-steps-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  gap: 8px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.6;
}

.workflow-step.active {
  opacity: 1;
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #2563eb;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-info {
  display: flex;
  flex-direction: column;
}

.step-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.step-desc {
  font-size: 11px;
  color: #64748b;
}

.step-arrow {
  color: #94a3b8;
  font-size: 12px;
}

/* 语义拆解表 */
.decomposition-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 12px 16px;
}

.decomp-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 6px;
  font-size: 13px;
}

.decomp-table th {
  background: #fef3c7;
  color: #92400e;
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid #fde68a;
}

.decomp-table td {
  padding: 8px 10px;
  border-bottom: 1px dashed #fde68a;
  color: #334155;
}

.decomp-table tr:last-child td {
  border-bottom: none;
}

.text-primary {
  color: #2563eb;
}

/* 证据卡片容器 */
.evidence-decision-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  overflow: hidden;
  transition: all 0.2s ease;
}

.evidence-decision-card.card-highlight {
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.card-top-bar {
  background: #f8fafc;
  padding: 10px 16px;
  border-bottom: 1px solid #e2e8f0;
}

.card-badge {
  background: #2563eb;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-title-en {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.card-content {
  padding: 14px 16px;
}

.field-row {
  margin-bottom: 10px;
}

.field-k {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.field-v {
  font-size: 13px;
  color: #1e293b;
}

/* 推荐理由提示框 */
.reason-banner {
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.reason-exact {
  background: #f0fdf4;
  border-left: 4px solid #16a34a;
  color: #15803d;
}

.reason-warning {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  color: #92400e;
}

.reason-head {
  font-weight: 700;
  margin-bottom: 4px;
}

.reason-body {
  font-size: 12.5px;
}

/* 原文引用框 */
.source-quote-box {
  background: #f1f5f9;
  border-left: 3px solid #64748b;
  padding: 8px 12px;
  border-radius: 4px;
  color: #334155;
  font-size: 12.5px;
  font-style: italic;
  line-height: 1.6;
  margin-top: 4px;
}

/* 左侧信源信息允许收缩换行（保留完整名称），把空间让给右侧链接 */
.source-meta {
  min-width: 0;
  flex: 1 1 auto;
}

.source-external-link {
  font-size: 12.5px;
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
  /* 不换行、不被左侧信源名挤扁：否则「查看站内检索结果 ↗」会被折成两行 */
  white-space: nowrap;
  flex-shrink: 0;
  margin-left: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #eff6ff;
  line-height: 1.5;
}

.source-external-link:hover {
  text-decoration: underline;
}

.ml-8 { margin-left: 8px; }
.mb-8 { margin-bottom: 8px; }
.mb-12 { margin-bottom: 12px; }
.font-bold { font-weight: 700; }
.text-muted { color: #64748b; }
.text-secondary { color: #475569; }
</style>
