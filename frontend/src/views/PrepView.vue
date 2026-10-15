<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeTerm, fetchAuthority } from '../api/modules'

const term = ref('')
const context = ref('')
const loading = ref(false)
const authLoading = ref(false)
const result = ref(null)
const authority = ref(null)

// 权威译文卡片的数据源：优先「仅取权威译文」的结果，其次查证结果里带回来的
const auth = computed(() => authority.value || result.value?.authority || null)
const authFound = computed(() => !!auth.value?.found)

const analyze = async () => {
  if (!term.value.trim()) {
    ElMessage.warning('请输入要查证的词语')
    return
  }
  loading.value = true
  authority.value = null
  try {
    result.value = (await analyzeTerm(term.value.trim(), context.value))?.data || null
  } finally {
    loading.value = false
  }
}

const onlyAuthority = async () => {
  if (!term.value.trim()) {
    ElMessage.warning('请输入要查证的词语')
    return
  }
  authLoading.value = true
  try {
    authority.value = (await fetchAuthority(term.value.trim()))?.data || null
  } finally {
    authLoading.value = false
  }
}

const copyTranslation = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('译文已复制')
  } catch (e) {
    ElMessage.warning('复制失败，请手动选择文本复制')
  }
}

const statusTag = (s) =>
  ({ locked: 'success', confirmed: 'warning', pending: 'info', conflict: 'danger', blocked: 'danger', invalid: 'info' }[s] || 'info')
const tierTag = (t) => (t === 'tier1' ? 'success' : t === 'tier2' ? 'warning' : 'danger')
const tierText = (t) => (t === 'tier1' ? '一级源' : t === 'tier2' ? '二级源' : t === 'tier3' ? '三级源（黑名单）' : t)

// 核验按钮文案：按该站真实能力区分，不给「看起来能搜其实搜不到」的假链接
const verifyLabel = (row) => {
  if (row.search_kind === 'site-detail') return '打开官网原始条目'
  if (row.search_kind === 'site-search') return '进官网检索'
  if (row.search_kind === 'form') return '打开查询系统'
  return '打开官网'
}
const kindTag = (k) =>
  ({ 'site-search': 'success', 'site-detail': 'success', form: 'warning', homepage: 'info' }[k] || 'info')
const kindText = (k) =>
  ({ 'site-search': '可站内检索', 'site-detail': '直取条目', form: '需手动查询', homepage: '无检索入口' }[k] || k)
const langText = (l) => ({ zh: '中文词', en: '英文译名', 'zh-fallback': '中文词（未取到英文译名）' }[l] || l)
const langTag = (l) => (l === 'en' ? 'success' : l === 'zh-fallback' ? 'warning' : 'primary')
</script>

<template>
  <div class="prep">
    <el-card shadow="never">
      <template #header><span class="card-title">译前准备 · 术语查证</span></template>
      <el-alert type="info" :closable="false" show-icon
        title="输入词语 → 系统判定领域 → 按「一级源优先，找不到再降二级，三级一律不用」直取权威信源，直接显示该词的官方英文译名与出处。" />
      <div class="prep__row">
        <el-input v-model="term" placeholder="要查证的词语，例如：水力压裂 / 碳中和 / 沉积岩" style="width: 380px" @keyup.enter="analyze" />
        <el-button type="primary" :loading="loading" @click="analyze">查证（判领域 + 取译文）</el-button>
        <el-button :loading="authLoading" @click="onlyAuthority">仅取权威译文</el-button>
      </div>
      <el-input v-model="context" type="textarea" :rows="3"
        placeholder="（可选）粘贴该词语所在的句子或段落，能显著提升领域判定准确度" />
    </el-card>

    <!-- ===== 权威译文显示卡片：页面直接给出译文，不给搜索界面 ===== -->
    <el-card v-if="auth" shadow="never" class="prep__auth">
      <template #header>
        <div class="prep__auth-head">
          <span class="card-title">权威译文</span>
          <el-tag v-if="authFound" type="success" size="small" effect="dark">一级源 · {{ auth.source_name }}</el-tag>
          <el-tag v-else type="info" size="small">一级源未收录</el-tag>
        </div>
      </template>

      <template v-if="authFound">
        <div class="prep__trans">
          <div class="prep__trans-cn">{{ auth.term }}</div>
          <div class="prep__trans-arrow">→</div>
          <div class="prep__trans-en">{{ auth.translation }}</div>
          <el-button size="small" text type="primary" @click="copyTranslation(auth.translation)">复制</el-button>
        </div>

        <div class="prep__tags">
          <el-tag v-for="v in auth.variants || []" :key="v" size="small" effect="plain" class="prep__tag">{{ v }}</el-tag>
        </div>

        <el-descriptions :column="2" size="small" border class="prep__desc">
          <el-descriptions-item label="术语库出处">{{ auth.termbase }}</el-descriptions-item>
          <el-descriptions-item label="所属学科">{{ auth.subject || '—' }}</el-descriptions-item>
          <el-descriptions-item label="发布年份">{{ auth.publish_year || '—' }}</el-descriptions-item>
          <el-descriptions-item label="术语编号">{{ auth.word_number || '—' }}</el-descriptions-item>
          <el-descriptions-item label="中文释义" :span="2">{{ auth.definition || '—' }}</el-descriptions-item>
          <el-descriptions-item v-if="auth.tw" label="台湾译名" :span="2">{{ auth.tw }}</el-descriptions-item>
          <el-descriptions-item v-if="auth.quote" label="审定依据" :span="2">{{ auth.quote }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="(auth.also_from || []).length" class="prep__also">
          <div class="prep__also-title">同词多库译名（均为一级源）</div>
          <el-table :data="auth.also_from" size="small" border>
            <el-table-column prop="translation" label="英文译名" min-width="200" />
            <el-table-column prop="termbase" label="术语库" min-width="200" />
          </el-table>
        </div>

        <div class="prep__actions">
          <el-link :href="auth.detail_url" target="_blank" type="primary">
            打开术语在线原始条目（{{ auth.termbase }}）
          </el-link>
        </div>
      </template>

      <template v-else>
        <el-alert type="warning" :closable="false" show-icon :title="auth.reason || '一级源未收录该词'" />
        <div class="prep__actions">
          <el-link :href="auth.homepage" target="_blank" type="info">打开术语在线首页</el-link>
          <span class="prep__gap"></span>
          <el-link :href="auth.search_url" target="_blank" type="info">在术语在线站内检索「{{ auth.term }}」</el-link>
        </div>
      </template>
    </el-card>

    <template v-if="result">
      <el-card shadow="never">
        <template #header><span class="card-title">① 领域判定</span></template>
        <div class="prep__domain">
          <el-tag size="large" type="primary">{{ result.domain?.domain_zh || '未识别' }}</el-tag>
          <span class="prep__conf">置信度 {{ result.domain?.confidence ?? 0 }}</span>
        </div>
        <div class="prep__hits" v-if="(result.domain?.matched_keywords || []).length">
          命中关键词：
          <el-tag v-for="k in result.domain.matched_keywords" :key="k" size="small" effect="plain" class="prep__kw">{{ k }}</el-tag>
        </div>
        <div class="prep__reason">{{ result.domain?.reason }}</div>
      </el-card>

      <el-card shadow="never">
        <template #header><span class="card-title">② 裁决结果</span></template>
        <div class="prep__verdict">
          <el-tag size="large" :type="statusTag(result.status)">{{ result.verdict_label || result.status }}</el-tag>
          <span v-if="result.translation" class="prep__translation">定译：<b>{{ result.translation }}</b></span>
        </div>
        <div class="prep__reason">{{ result.reason || result.message }}</div>
      </el-card>

      <el-card shadow="never" v-if="(result.evidence || []).length">
        <template #header><span class="card-title">③ 权威信源证据链</span></template>
        <el-alert type="info" :closable="false" class="prep__tip"
          title="每个信源用哪个词检索、能不能真的检索到，都在表里如实标注。英文站（中国政府网英文版、教育部英文官网）必须用英文译名，用中文词是搜不到的；没有检索入口的站点直接标为「无检索入口」，不给你一个点了没结果的链接。" />
        <el-table :data="result.evidence" size="small" border stripe>
          <el-table-column prop="text" label="译文" min-width="160" />
          <el-table-column label="等级" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="tierTag(row.tier)">{{ tierText(row.tier) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source_name" label="信源" min-width="140" />
          <el-table-column prop="termbase" label="术语库 / 出处" min-width="140" />
          <el-table-column prop="snippet" label="证明 / 释义" min-width="200" show-overflow-tooltip />
          <el-table-column label="该站检索词" min-width="190">
            <template #default="{ row }">
              <div v-if="row.search_query" class="prep__q">
                <span class="prep__q-text">{{ row.search_query }}</span>
                <el-tag size="small" effect="plain" :type="langTag(row.search_lang)">
                  {{ langText(row.search_lang) }}
                </el-tag>
              </div>
              <span v-else class="prep__q-none">—</span>
            </template>
          </el-table-column>
          <el-table-column label="核验" min-width="160">
            <template #default="{ row }">
              <div class="prep__verify">
                <el-tag size="small" :type="kindTag(row.search_kind)" effect="plain">
                  {{ kindText(row.search_kind) }}
                </el-tag>
                <el-link v-if="row.search_url" :href="row.search_url" target="_blank" type="primary">
                  {{ verifyLabel(row) }}
                </el-link>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" v-if="(result.searchPlan || []).length">
        <template #header><span class="card-title">④ 分级查证方案（一级源未收录，按此降级核查）</span></template>
        <div v-for="r in result.searchPlan" :key="r.tier" class="prep__round">
          <div class="prep__round-head">
            <el-tag :type="tierTag(r.tier)" size="small">{{ r.label }}</el-tag>
            <span class="prep__round-note" v-if="r.note">{{ r.note }}</span>
            <span class="prep__round-note" v-else>共 {{ r.count }} 个信源</span>
          </div>
          <el-table v-if="(r.sources || []).length" :data="r.sources" size="small" border>
            <el-table-column prop="name" label="信源" min-width="150" />
            <el-table-column prop="affiliation" label="归属" min-width="110" />
            <el-table-column label="该站检索词" min-width="190">
              <template #default="{ row }">
                <div v-if="row.search_query" class="prep__q">
                  <span class="prep__q-text">{{ row.search_query }}</span>
                  <el-tag size="small" effect="plain" :type="langTag(row.search_lang)">
                    {{ langText(row.search_lang) }}
                  </el-tag>
                </div>
                <span v-else class="prep__q-none">—</span>
              </template>
            </el-table-column>
            <el-table-column label="核验" min-width="170">
              <template #default="{ row }">
                <div class="prep__verify">
                  <el-tag size="small" :type="kindTag(row.search_kind)" effect="plain">
                    {{ kindText(row.search_kind) }}
                  </el-tag>
                  <el-link v-if="row.search_url" :href="row.search_url" target="_blank" type="primary">
                    {{ verifyLabel(row) }}
                  </el-link>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <el-card shadow="never" v-if="result.policy">
        <template #header><span class="card-title">⑤ 信源使用策略</span></template>
        <ul class="prep__policy">
          <li><b>一级源</b>：{{ result.policy.tier1 }}</li>
          <li><b>二级源</b>：{{ result.policy.tier2 }}</li>
          <li><b>三级源</b>：{{ result.policy.tier3 }}</li>
          <li><b>未覆盖</b>：{{ result.policy.unmatched }}</li>
        </ul>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.card-title { font-weight: 500; }
.prep { display: flex; flex-direction: column; gap: 16px; }
.prep__row { display: flex; gap: 12px; margin: 16px 0 12px; }

.prep__auth-head { display: flex; align-items: center; gap: 10px; }
.prep__trans { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.prep__trans-cn { font-size: 22px; font-weight: 600; color: var(--el-text-color-primary); }
.prep__trans-arrow { font-size: 20px; color: var(--el-text-color-secondary); }
.prep__trans-en { font-size: 26px; font-weight: 700; color: var(--el-color-success); letter-spacing: 0.3px; }
.prep__tags { margin: 12px 0 4px; display: flex; flex-wrap: wrap; gap: 8px; }
.prep__tag { font-family: Consolas, Menlo, monospace; }
.prep__desc { margin-top: 12px; }
.prep__also { margin-top: 14px; }
.prep__also-title { font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 8px; }
.prep__actions { margin-top: 14px; display: flex; align-items: center; }
.prep__gap { display: inline-block; width: 16px; }

.prep__domain { display: flex; align-items: center; gap: 12px; }
.prep__conf { font-size: 13px; color: var(--el-text-color-secondary); }
.prep__hits { margin-top: 10px; font-size: 13px; color: var(--el-text-color-regular); }
.prep__kw { margin-left: 6px; }
.prep__reason { margin-top: 10px; font-size: 13px; color: var(--el-text-color-secondary); }
.prep__verdict { display: flex; align-items: center; gap: 16px; }
.prep__translation { font-size: 15px; }
.prep__tip { margin-bottom: 12px; }
.prep__q { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.prep__q-text { font-family: Consolas, Menlo, monospace; font-size: 12px; }
.prep__q-none { color: var(--el-text-color-placeholder); }
.prep__verify { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.prep__round { margin-bottom: 18px; }
.prep__round-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.prep__round-note { font-size: 12px; color: var(--el-text-color-secondary); }
.prep__sources { display: flex; flex-wrap: wrap; gap: 8px 18px; }
.prep__source { font-size: 13px; }
.prep__policy { margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.9; color: var(--el-text-color-regular); }
</style>
