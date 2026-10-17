<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchModels } from '../api/modules'

const models = ref([])
const draft = ref('')
const review = ref('')
const arbitrate = ref('')

const byId = (id) => models.value.find((m) => m.id === id) || null
const draftModel = computed(() => byId(draft.value))
const reviewModel = computed(() => byId(review.value))
const arbitrateModel = computed(() => byId(arbitrate.value))

const capStars = (n) => '★'.repeat(n) + '☆'.repeat(Math.max(0, 5 - n))

// 架构族：只有 arch_family 不同才算真正异构；老数据没有该字段时退回 architecture 文本
const famOf = (m) => m.arch_family || m.architecture
const famLabel = (m) => m.arch_family_label || m.architecture

const heteroWarning = computed(() => {
  const a = draftModel.value
  const b = reviewModel.value
  if (!a || !b) return ''
  if (a.vendor === b.vendor) return `复核与主译同属「${a.vendor}」，同源模型容易同错，互校会失效，请换一家厂商`
  if (famOf(a) === famOf(b)) return `复核与主译同属「${famLabel(a)}」架构族，同架构互校容易同错，建议换一个架构族`
  return ''
})

const load = async () => {
  const data = (await fetchModels())?.data || {}
  models.value = data.models || []
  const d = data.default_roles || {}
  draft.value = byId(d.draft) ? d.draft : (models.value[0]?.id || '')
  review.value = byId(d.review) ? d.review : (models.value[1]?.id || '')
  arbitrate.value = byId(d.arbitrate) ? d.arbitrate : (models.value[2]?.id || '')
}

// 与后端 /api/review/diff 对接；当前为静态演示数据
const segments = ref([
  {
    id: 1,
    source: '西南石油大学创建于1958年，是新中国第二所石油本科院校。',
    draftA: 'Southwest Petroleum University was founded in 1958 as the second petroleum undergraduate institution of New China.',
    draftB: 'Founded in 1958, Southwest Petroleum University became the second petroleum undergraduate college in New China.',
    verdict: 'draftA',
    type: '语序',
    reason: 'B 译法把 founded in 1958 提前，弱化了「创建于」的时间信息焦点，A 更符合纪年表述习惯。'
  },
  {
    id: 2,
    source: '学校先后更名为四川石油学院、西南石油学院，2005年定名西南石油大学。',
    draftA: 'The university was successively renamed Sichuan Petroleum Institute and Southwest Petroleum Institute, and was named Southwest Petroleum University in 2005.',
    draftB: 'It was later renamed Sichuan Petroleum Institute, then Southwest Petroleum Institute, and in 2005 settled on its current name.',
    verdict: 'pending',
    type: '术语',
    reason: '「定名」两译均可，需查证一级源（学校官网英文简介）后锁定，当前置为待定。'
  }
])

const typeTag = (t) => ({ 术语: 'danger', 语序: 'warning', 省略: 'info', 语气: 'success' }[t] || 'info')

onMounted(load)
</script>

<template>
  <div class="review">
    <el-card shadow="never">
      <template #header><span class="card-title">校对模型选择（互校须跨厂商、跨架构）</span></template>
      <el-alert type="info" :closable="false" show-icon class="review__tip"
        title="不熟悉大模型的同学看这里：★ 越多越聪明。主译负责初译，复核独立重译后与主译比对，裁决对分歧做最终裁定。" />

      <el-row :gutter="16" class="review__roles">
        <el-col :span="8">
          <div class="role-box">
            <div class="role-box__title">主译 <span class="role-box__desc">初译 · 精准无错</span></div>
            <el-select v-model="draft" placeholder="选择主译模型" style="width: 100%">
              <el-option v-for="m in models" :key="m.id"
                :label="`${m.name} · ${capStars(m.capability)}`" :value="m.id" />
            </el-select>
            <div v-if="draftModel" class="role-box__meta">
              <div class="role-box__caps">{{ capStars(draftModel.capability) }} {{ draftModel.capability_label }}</div>
              <div class="role-box__line">{{ draftModel.capability_desc }}</div>
              <div class="role-box__line">厂商：{{ draftModel.vendor }}</div>
              <div class="role-box__line">架构：{{ draftModel.architecture }}</div>
              <div class="role-box__line">上下文：{{ draftModel.context }} ｜ API 名：<code>{{ draftModel.api_model }}</code></div>
              <el-tag size="small" :type="draftModel.configured ? 'success' : 'info'">
                {{ draftModel.configured ? '已配置 Key' : '待配置 Key' }}
              </el-tag>
            </div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="role-box">
            <div class="role-box__title">复核 <span class="role-box__desc">独立重译 · 比对分歧</span></div>
            <el-select v-model="review" placeholder="选择复核模型" style="width: 100%">
              <el-option v-for="m in models" :key="m.id"
                :label="`${m.name} · ${capStars(m.capability)}`" :value="m.id" />
            </el-select>
            <div v-if="reviewModel" class="role-box__meta">
              <div class="role-box__caps">{{ capStars(reviewModel.capability) }} {{ reviewModel.capability_label }}</div>
              <div class="role-box__line">{{ reviewModel.capability_desc }}</div>
              <div class="role-box__line">厂商：{{ reviewModel.vendor }}</div>
              <div class="role-box__line">架构：{{ reviewModel.architecture }}</div>
              <div class="role-box__line">上下文：{{ reviewModel.context }} ｜ API 名：<code>{{ reviewModel.api_model }}</code></div>
              <el-tag size="small" :type="reviewModel.configured ? 'success' : 'info'">
                {{ reviewModel.configured ? '已配置 Key' : '待配置 Key' }}
              </el-tag>
            </div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="role-box">
            <div class="role-box__title">裁决 <span class="role-box__desc">最终裁定 · 建议最强</span></div>
            <el-select v-model="arbitrate" placeholder="选择裁决模型" style="width: 100%">
              <el-option v-for="m in models" :key="m.id"
                :label="`${m.name} · ${capStars(m.capability)}`" :value="m.id" />
            </el-select>
            <div v-if="arbitrateModel" class="role-box__meta">
              <div class="role-box__caps">{{ capStars(arbitrateModel.capability) }} {{ arbitrateModel.capability_label }}</div>
              <div class="role-box__line">{{ arbitrateModel.capability_desc }}</div>
              <div class="role-box__line">厂商：{{ arbitrateModel.vendor }}</div>
              <div class="role-box__line">架构：{{ arbitrateModel.architecture }}</div>
              <div class="role-box__line">上下文：{{ arbitrateModel.context }} ｜ API 名：<code>{{ arbitrateModel.api_model }}</code></div>
              <el-tag size="small" :type="arbitrateModel.configured ? 'success' : 'info'">
                {{ arbitrateModel.configured ? '已配置 Key' : '待配置 Key' }}
              </el-tag>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-alert v-if="heteroWarning" type="warning" :closable="false" show-icon class="review__warn"
        :title="heteroWarning" />
    </el-card>

    <el-card v-for="seg in segments" :key="seg.id" shadow="never" class="review__card">
      <template #header>
        <div class="review__head">
          <span class="review__id">#{{ seg.id }}</span>
          <el-tag :type="typeTag(seg.type)" size="small">{{ seg.type }}分歧</el-tag>
          <el-tag size="small" :type="seg.verdict === 'pending' ? 'info' : 'success'">
            {{ seg.verdict === 'pending' ? '待人工确认' : '已裁决' }}
          </el-tag>
        </div>
      </template>

      <p class="review__source"><span>原文</span>{{ seg.source }}</p>
      <div class="review__compare">
        <div class="review__draft">
          <div class="review__label">主译稿 · {{ draftModel?.name || '模型 A' }}</div>
          <p>{{ seg.draftA }}</p>
        </div>
        <div class="review__draft">
          <div class="review__label">复核稿 · {{ reviewModel?.name || '模型 B' }}</div>
          <p>{{ seg.draftB }}</p>
        </div>
      </div>
      <div class="review__reason"><span>裁决理由</span>{{ seg.reason }}</div>
    </el-card>
  </div>
</template>

<style scoped>
.card-title { font-weight: 500; }
.review { display: flex; flex-direction: column; gap: 16px; }
.review__tip { margin-bottom: 16px; }
.review__roles { margin-bottom: 4px; }
.role-box { border: 1px solid var(--el-border-color-light); border-radius: 8px; padding: 14px; height: 100%; }
.role-box__title { font-weight: 500; margin-bottom: 10px; }
.role-box__desc { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 6px; font-weight: 400; }
.role-box__meta { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.role-box__caps { color: var(--el-color-warning); font-size: 14px; }
.role-box__line { font-size: 12px; color: var(--el-text-color-regular); line-height: 1.6; }
.role-box__line code {
  font-family: var(--el-font-family-mono, ui-monospace, Consolas, monospace);
  background: var(--el-fill-color); padding: 1px 4px; border-radius: 3px; font-size: 11px;
}
.review__warn { margin-top: 16px; }
.review__head { display: flex; align-items: center; gap: 8px; }
.review__id { font-weight: 500; }
.review__source span, .review__reason span {
  display: inline-block; font-size: 12px; color: var(--el-text-color-secondary); margin-right: 8px;
}
.review__source { margin: 0 0 12px; font-weight: 500; }
.review__compare { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.review__draft { background: var(--el-fill-color-light); border-radius: 8px; padding: 12px; }
.review__label { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 6px; }
.review__draft p { margin: 0; font-size: 13px; line-height: 1.6; }
.review__reason { margin-top: 12px; font-size: 13px; }
</style>
