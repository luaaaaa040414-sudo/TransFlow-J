<template>
  <div class="proofread-view">
    <!-- Apple-style Sub-navigation Bar -->
    <ProjectHeaderNav :project-id="id" current-tab="proofread" />

    <div class="page-header flex-between mb-24">
      <div>
        <div class="page-title">🔬 多模型 MQM 校对</div>
        <div class="page-desc">选择独立校对模型，发现准确性、流畅性、术语等 MQM 类问题</div>
      </div>
      <el-button type="success" @click="generateReport" :loading="generatingReport">
        <el-icon><Document /></el-icon> 生成质量报告
      </el-button>
    </div>

    <!-- 校对模型选择 -->
    <div class="card mb-24">
      <div class="flex-between">
        <strong>校对模型配置</strong>
        <span style="font-size: 12px; color: #888;">支持 DeepSeek / 仿真演示 / OpenAI / Claude 等多模型独立复核</span>
      </div>
      <div class="flex gap-8 mt-16" style="align-items: center; flex-wrap: wrap;">
        <el-select v-model="proofProvider" style="width: 200px">
          <el-option label="DeepSeek (推荐/已就绪)" value="deepseek" />
          <el-option label="学术仿真演示 (免Key)" value="simulation" />
          <el-option label="OpenAI (需配置Key)" value="openai" />
          <el-option label="Claude (需配置Key)" value="anthropic" />
          <el-option label="自定义兼容接口" value="custom" />
        </el-select>
        <el-input v-model="proofModel" placeholder="模型 ID" style="width: 180px" />
        <el-button @click="testProofConnection" :loading="testingProofConn">
          <el-icon><Connection /></el-icon> 测试连接
        </el-button>
        <el-button link type="primary" @click="$router.push('/models')" style="font-size: 13px;">
          ⚙️ 配置Key
        </el-button>
        <el-alert
          type="info" :closable="false"
          title="建议选择独立校对模型（如 DeepSeek 或学术仿真），进行跨视角 MQM 缺陷检测"
          style="flex: 1; min-width: 320px; margin: 0;"
        />
      </div>
    </div>

    <!-- 段落校对列表 -->
    <div class="card mb-24">
      <div class="flex-between mb-16">
        <div class="flex gap-12" style="align-items: center;">
          <strong>段落校对</strong>
          <span v-if="batchProgress" style="font-size: 13px; color: #409eff; font-weight: 500;">{{ batchProgress }}</span>
        </div>
        <div class="flex gap-8">
          <el-button
            type="primary"
            size="small"
            :loading="batchProofreading"
            @click="proofreadAll"
          >
            <el-icon><Search /></el-icon> 一键校对全篇 ({{ segments.filter(s => !!s.translated_text).length }}段)
          </el-button>
          <el-select v-model="issueFilter" placeholder="问题筛选" clearable style="width:130px" @change="loadIssues">
            <el-option label="全部" value="" />
            <el-option label="待裁决" value="pending" />
            <el-option label="已采纳" value="accepted" />
            <el-option label="已修改" value="modified" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </div>
      </div>

      <el-table :data="segments" v-loading="loadingSegs" stripe size="small">
        <el-table-column prop="segment_id" label="编号" width="80" />
        <el-table-column prop="section" label="章节" width="100" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span :class="`status-badge status-${row.status}`">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="原文（摘要）" min-width="180">
          <template #default="{ row }">
            <span style="font-size:13px; color:#555">{{ row.source_text?.slice(0, 60) }}...</span>
          </template>
        </el-table-column>
        <el-table-column label="译文（摘要）" min-width="180">
          <template #default="{ row }">
            <span v-if="row.translated_text" style="font-size:13px; color:#333">
              {{ row.translated_text?.slice(0, 60) }}...
            </span>
            <span v-else style="color:#aaa; font-size:13px;">未翻译</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              :disabled="!row.translated_text"
              :loading="proofingIds.includes(row.id)"
              @click="proofreadSegment(row)"
            >
              <el-icon><Search /></el-icon> 校对
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 问题列表 -->
    <div class="card mb-24">
      <div class="flex-between mb-16">
        <strong>MQM 问题列表</strong>
        <div class="flex gap-8">
          <el-tag type="danger">Critical: {{ issueStats.critical }}</el-tag>
          <el-tag type="warning">Major: {{ issueStats.major }}</el-tag>
          <el-tag type="info">Minor: {{ issueStats.minor }}</el-tag>
          <el-tag>待裁决: {{ issueStats.pending }}</el-tag>
        </div>
      </div>

      <div v-if="issues.length === 0 && !loadingIssues" style="text-align:center; padding:30px;">
        <el-empty description="暂无校对问题，请先对段落进行校对" :image-size="60" />
      </div>

      <div v-loading="loadingIssues">
        <div v-for="issue in issues" :key="issue.id" class="issue-card">
          <div class="issue-header">
            <div class="flex gap-8" style="align-items:center;">
              <span :class="`severity-badge severity-${issue.severity}`">
                {{ issue.severity.toUpperCase() }}
              </span>
              <el-tag size="small" type="warning">{{ issue.error_type }}</el-tag>
              <span v-if="issue.error_subtype" style="font-size:12px; color:#888">/ {{ issue.error_subtype }}</span>
              <span style="font-size:12px; color:#aaa">By {{ issue.detected_by }}</span>
            </div>
            <span :class="`status-badge status-${issue.human_status}`">
              {{ issueStatusLabel(issue.human_status) }}
            </span>
          </div>

          <div class="issue-body">
            <div v-if="issue.source_span" class="span-block source-span">
              <span class="span-label">原文</span>「{{ issue.source_span }}」
            </div>
            <div v-if="issue.translation_span" class="span-block trans-span">
              <span class="span-label">译文</span>「{{ issue.translation_span }}」
            </div>
            <div class="issue-explanation">{{ issue.explanation }}</div>
            <div v-if="issue.suggested_revision" class="suggested-revision">
              <span class="span-label">建议</span> {{ issue.suggested_revision }}
            </div>
            <div v-if="issue.evidence" class="issue-evidence">
              <span class="span-label">依据</span> {{ issue.evidence }}
            </div>
          </div>

          <!-- 裁决按钮 -->
          <div v-if="issue.human_status === 'pending'" class="issue-actions">
            <el-input
              v-model="decisionTexts[issue.id]"
              placeholder="裁决说明（可选）"
              size="small"
              style="width: 300px"
            />
            <el-button size="small" type="success" @click="decide(issue, 'accepted')">
              ✓ 采纳
            </el-button>
            <el-button size="small" type="primary" @click="openModifyDialog(issue)">
              ✏ 修改并采纳
            </el-button>
            <el-button size="small" @click="decide(issue, 'rejected')">
              ✗ 拒绝
            </el-button>
          </div>
          <div v-else class="issue-decided">
            {{ issue.human_decision_text || '已裁决' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 最新质量报告 -->
    <div v-if="latestReport" class="card">
      <strong>📊 质量报告（{{ formatDate(latestReport.generated_at) }}）</strong>
      <div class="report-grid mt-16">
        <div class="report-metric" :class="latestReport.quality?.number_errors_pass ? 'pass' : 'fail'">
          <div class="metric-label">数字一致性</div>
          <div class="metric-value">{{ latestReport.quality?.number_errors_pass ? '✓ 通过' : `✗ ${latestReport.quality?.number_errors} 处错误` }}</div>
        </div>
        <div class="report-metric" :class="(latestReport.quality?.terminology_consistency_rate >= 0.98) ? 'pass' : 'warn'">
          <div class="metric-label">术语一致率</div>
          <div class="metric-value">{{ latestReport.quality?.terminology_consistency_rate != null ? (latestReport.quality.terminology_consistency_rate * 100).toFixed(1) + '%' : 'N/A' }}</div>
        </div>
        <div class="report-metric">
          <div class="metric-label">校对建议采纳率</div>
          <div class="metric-value">{{ latestReport.quality?.adoption_rate != null ? (latestReport.quality.adoption_rate * 100).toFixed(1) + '%' : 'N/A' }}</div>
        </div>
        <div class="report-metric">
          <div class="metric-label">人工修改率</div>
          <div class="metric-value">{{ latestReport.quality?.human_edit_rate != null ? (latestReport.quality.human_edit_rate * 100).toFixed(1) + '%' : 'N/A' }}</div>
        </div>
        <div class="report-metric" :class="latestReport.issues?.pending === 0 ? 'pass' : 'warn'">
          <div class="metric-label">未解决问题</div>
          <div class="metric-value">{{ latestReport.issues?.pending || 0 }} 项</div>
        </div>
        <div class="report-metric">
          <div class="metric-label">检查范围</div>
          <div class="metric-value" style="font-size:14px;">{{ latestReport.summary?.translated_segments }} 个段落</div>
        </div>
      </div>

      <!-- 数字差异明细列表 -->
      <div v-if="latestReport.detail?.number_issues_detail?.length" class="mt-16 number-issues-box">
        <div style="font-weight: 600; color: #cf1322; margin-bottom: 8px;">
          ⚠ 发现 {{ latestReport.detail.number_issues_detail.length }} 处数字差异核对提示：
        </div>
        <div v-for="(numIssue, idx) in latestReport.detail.number_issues_detail" :key="idx" class="number-issue-detail-item">
          <el-tag type="danger" size="small" style="margin-right: 8px;">段落 {{ numIssue.segment_id }}</el-tag>
          <span>{{ numIssue.description }}</span>
        </div>
      </div>

      <el-alert
        v-if="latestReport.quality?.number_errors === 0 && latestReport.issues?.pending === 0"
        type="success"
        title="✅ 全部检查项通过，可进行最终导出"
        :closable="false"
        class="mt-16"
        show-icon
      />
    </div>

    <!-- 成果导出与过程归档 -->
    <div class="card mt-24 mb-24">
      <div class="flex-between mb-16">
        <div>
          <strong style="font-size:16px;">📥 成果导出与翻译过程归档</strong>
          <div style="font-size:13px; color:#888; margin-top:4px;">
            满足学术期刊投稿与质量保障流程总表要求的全套材料
          </div>
        </div>
      </div>
      <div class="flex gap-16 flex-wrap">
        <a :href="exportApi.englishDocxUrl(id)" target="_blank" style="text-decoration:none;">
          <el-button type="primary" size="large">
            <el-icon><Document /></el-icon> 纯英文学术论文 (.docx)
          </el-button>
        </a>
        <a :href="exportApi.bilingualDocxUrl(id)" target="_blank" style="text-decoration:none;">
          <el-button type="info" size="large">
            <el-icon><DocumentCopy /></el-icon> 中英逐段对照审校稿 (.docx)
          </el-button>
        </a>
        <a :href="exportApi.terminologyXlsxUrl(id)" target="_blank" style="text-decoration:none;">
          <el-button type="success" size="large">
            <el-icon><Tickets /></el-icon> 术语表与信源证据表 (.xlsx)
          </el-button>
        </a>
        <a :href="exportApi.mqmXlsxUrl(id)" target="_blank" style="text-decoration:none;">
          <el-button type="warning" size="large">
            <el-icon><Finished /></el-icon> MQM错误清单与裁决 (.xlsx)
          </el-button>
        </a>
        <a :href="exportApi.archiveZipUrl(id)" target="_blank" style="text-decoration:none;">
          <el-button type="danger" size="large">
            <el-icon><FolderChecked /></el-icon> 全流程可复现归档包 (.zip)
          </el-button>
        </a>
      </div>
    </div>

    <!-- 修改并采纳对话框 -->
    <el-dialog v-model="showModifyDialog" title="修改并采纳" width="560px">
      <div v-if="modifyIssue">
        <div class="mb-16">
          <div class="span-label">校对建议</div>
          <div class="suggested-revision">{{ modifyIssue.suggested_revision }}</div>
        </div>
        <el-form>
          <el-form-item label="最终译文">
            <el-input v-model="modifyFinalText" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="修改理由">
            <el-input v-model="modifyReason" placeholder="可选：说明修改原因" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showModifyDialog = false">取消</el-button>
        <el-button type="primary" @click="doModify" :loading="modifying">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Search, DocumentCopy, Tickets, Finished, FolderChecked, Connection } from '@element-plus/icons-vue'
import ProjectHeaderNav from '../components/ProjectHeaderNav.vue'
import { translationApi, proofreadingApi, reportsApi, exportApi } from '../api'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const segments = ref<any[]>([])
const issues = ref<any[]>([])
const loadingSegs = ref(false)
const loadingIssues = ref(false)
const proofingIds = ref<number[]>([])
const proofProvider = ref('deepseek')
const proofModel = ref('deepseek-chat')
const testingProofConn = ref(false)
const issueFilter = ref('')
const decisionTexts = ref<Record<number, string>>({})
const latestReport = ref<any>(null)
const generatingReport = ref(false)
const batchProofreading = ref(false)
const batchProgress = ref('')

watch(proofProvider, (newP) => {
  if (newP === 'deepseek') proofModel.value = 'deepseek-chat'
  else if (newP === 'simulation') proofModel.value = 'academic-simulation'
  else if (newP === 'openai') proofModel.value = 'gpt-4o'
  else if (newP === 'anthropic') proofModel.value = 'claude-3-5-sonnet-20241022'
  else if (newP === 'custom') proofModel.value = 'custom-model'
})

const testProofConnection = async () => {
  testingProofConn.value = true
  try {
    const res = await translationApi.testConnection(proofProvider.value, proofModel.value) as any
    if (res.success) {
      ElMessage.success(`校对模型连接成功！响应：${res.response?.slice(0, 30)}`)
    } else {
      ElMessage.error(`连接失败：${res.error}`)
    }
  } catch (e: any) {
    ElMessage.error(`连接失败：${e.message}`)
  } finally {
    testingProofConn.value = false
  }
}

const showModifyDialog = ref(false)
const modifyIssue = ref<any>(null)
const modifyFinalText = ref('')
const modifyReason = ref('')
const modifying = ref(false)

const issueStats = computed(() => ({
  critical: issues.value.filter(i => i.severity === 'critical').length,
  major: issues.value.filter(i => i.severity === 'major').length,
  minor: issues.value.filter(i => i.severity === 'minor').length,
  pending: issues.value.filter(i => i.human_status === 'pending').length,
}))

const statusLabel = (s: string) => ({ pending: '待翻译', translated: '已翻译', reviewing: '校对中', approved: '已审定', flagged: '已标记' }[s] || s)
const issueStatusLabel = (s: string) => ((({ pending: '待裁决', accepted: '已采纳', rejected: '已拒绝', modified: '已修改' } as Record<string, string>)[s]) || s)
const formatDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadSegments = async () => {
  loadingSegs.value = true
  try {
    segments.value = await translationApi.listSegments(id.value, { limit: 200 }) as any[]
  } finally {
    loadingSegs.value = false
  }
}

const loadIssues = async () => {
  loadingIssues.value = true
  try {
    const params: any = {}
    if (issueFilter.value) params.status = issueFilter.value
    issues.value = await proofreadingApi.listIssues(id.value, params) as any[]
  } finally {
    loadingIssues.value = false
  }
}

const proofreadSegment = async (seg: any) => {
  proofingIds.value.push(seg.id)
  try {
    const result = await proofreadingApi.proofreadSegment(seg.id, proofProvider.value, proofModel.value) as any
    // 关键修复：立即在前端更新响应式状态，无需刷新网页！
    seg.status = (result.issue_count === 0) ? 'approved' : 'reviewing'
    ElMessage.success(`${seg.segment_id} 校对完成，发现 ${result.issue_count} 个问题`)
    await loadIssues()
    await loadSegments()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    proofingIds.value = proofingIds.value.filter(i => i !== seg.id)
  }
}

const proofreadAll = async () => {
  const transSegs = segments.value.filter(s => !!s.translated_text)
  if (!transSegs.length) {
    ElMessage.warning('没有可校对的已翻译段落')
    return
  }
  batchProofreading.value = true
  let successCount = 0
  let totalIssues = 0
  try {
    for (let i = 0; i < transSegs.length; i++) {
      const seg = transSegs[i]
      batchProgress.value = `(${i + 1}/${transSegs.length}) 正在校对 ${seg.segment_id}...`
      proofingIds.value.push(seg.id)
      try {
        const res = await proofreadingApi.proofreadSegment(seg.id, proofProvider.value, proofModel.value) as any
        seg.status = (res.issue_count === 0) ? 'approved' : 'reviewing'
        successCount++
        totalIssues += (res.issue_count || 0)
      } catch (err: any) {
        console.error(`Proofread failed for ${seg.segment_id}:`, err)
      } finally {
        proofingIds.value = proofingIds.value.filter(itemId => itemId !== seg.id)
      }
    }
    ElMessage.success(`全篇校对完成！共校对 ${successCount} 个段落，发现 ${totalIssues} 个问题`)
    await loadIssues()
    await loadSegments()
  } catch (e: any) {
    ElMessage.error(`批量校对中断：${e.message}`)
  } finally {
    batchProofreading.value = false
    batchProgress.value = ''
  }
}

const decide = async (issue: any, status: string) => {
  try {
    let finalText: string | undefined = undefined
    const seg = segments.value.find(s => s.id === issue.segment_id_fk)
    if (status === 'accepted' && issue.suggested_revision && seg && seg.translated_text) {
      if (issue.translation_span && seg.translated_text.includes(issue.translation_span)) {
        finalText = seg.translated_text.replace(issue.translation_span, issue.suggested_revision)
      }
    }
    await proofreadingApi.decideIssue(issue.id, {
      human_status: status,
      human_decision_text: decisionTexts.value[issue.id] || null,
      final_text: finalText,
    })
    issue.human_status = status
    ElMessage.success(`已标记：${{ accepted: '采纳', rejected: '拒绝' }[status]}`)
    await loadIssues()
    await loadSegments()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const openModifyDialog = (issue: any) => {
  modifyIssue.value = issue
  const seg = segments.value.find(s => s.id === issue.segment_id_fk)
  if (seg && seg.translated_text) {
    if (issue.translation_span && seg.translated_text.includes(issue.translation_span)) {
      modifyFinalText.value = seg.translated_text.replace(issue.translation_span, issue.suggested_revision || '')
    } else {
      modifyFinalText.value = seg.translated_text
    }
  } else {
    modifyFinalText.value = issue.suggested_revision || ''
  }
  modifyReason.value = ''
  showModifyDialog.value = true
}

const doModify = async () => {
  if (!modifyFinalText.value) {
    ElMessage.warning('请填写最终译文')
    return
  }
  modifying.value = true
  try {
    await proofreadingApi.decideIssue(modifyIssue.value.id, {
      human_status: 'modified',
      human_decision_text: modifyReason.value,
      final_text: modifyFinalText.value,
    })
    modifyIssue.value.human_status = 'modified'
    showModifyDialog.value = false
    ElMessage.success('已修改并保存')
    await loadIssues()
    await loadSegments()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    modifying.value = false
  }
}

const generateReport = async () => {
  generatingReport.value = true
  try {
    latestReport.value = await reportsApi.generate(id.value) as any
    ElMessage.success('质量报告已生成')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    generatingReport.value = false
  }
}

const loadLatestReport = async () => {
  try {
    const list = await reportsApi.list(id.value) as any[]
    if (list && list.length > 0) {
      const rep = list[0]
      latestReport.value = {
        report_id: rep.id,
        project_id: rep.project_id,
        generated_at: rep.generated_at,
        summary: {
          total_segments: rep.total_segments,
          translated_segments: rep.translated_segments,
          approved_segments: rep.approved_segments,
          flagged_segments: rep.flagged_segments,
          progress_percent: rep.total_segments > 0 ? Math.round(rep.translated_segments / rep.total_segments * 100) : 0,
        },
        quality: {
          number_errors: rep.number_errors,
          number_errors_pass: rep.number_errors === 0,
          terminology_consistency_rate: rep.terminology_consistency_rate,
          terminology_pass: rep.terminology_consistency_rate === null || rep.terminology_consistency_rate >= 0.98,
          adoption_rate: rep.adoption_rate,
          human_edit_rate: rep.human_edit_rate,
        },
        issues: {
          total: rep.total_issues,
          critical: rep.critical_issues,
          major: rep.major_issues,
          minor: rep.minor_issues,
          resolved: rep.resolved_issues,
          pending: rep.total_issues - rep.resolved_issues,
        },
        detail: rep.report_data || {},
      }
    }
  } catch (e) {
    // ignore
  }
}

onMounted(async () => {
  await Promise.all([loadSegments(), loadIssues(), loadLatestReport()])
})
</script>

<style scoped>
.number-issues-box {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  padding: 12px 16px;
}
.number-issue-detail-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #333;
  margin-top: 6px;
}
.issue-card {
  border: 1px solid #e8edf3;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fff;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}

.issue-body {
  margin-bottom: 12px;
}

.span-block {
  font-size: 13px;
  margin-bottom: 6px;
  padding: 4px 8px;
  border-radius: 4px;
}

.source-span { background: #f0f4f8; color: #333; }
.trans-span { background: #fff7e6; color: #555; }

.span-label {
  font-size: 12px;
  font-weight: 700;
  color: #888;
  margin-right: 6px;
  text-transform: uppercase;
}

.issue-explanation {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 8px 0;
}

.suggested-revision {
  font-size: 13px;
  color: #0958d9;
  background: #e6f4ff;
  padding: 6px 10px;
  border-radius: 4px;
  margin: 4px 0;
}

.issue-evidence {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.issue-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f0f4f8;
  flex-wrap: wrap;
}

.issue-decided {
  font-size: 12px;
  color: #aaa;
  padding-top: 8px;
  border-top: 1px solid #f5f5f5;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.report-metric {
  padding: 14px;
  border: 1px solid #e8edf3;
  border-radius: 8px;
  text-align: center;
}

.report-metric.pass {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.report-metric.fail {
  border-color: #ffa39e;
  background: #fff1f0;
}

.report-metric.warn {
  border-color: #ffd591;
  background: #fff7e6;
}

.metric-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.mt-16 { margin-top: 16px; }
.mb-16 { margin-bottom: 16px; }
</style>
