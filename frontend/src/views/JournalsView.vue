<template>
  <div class="journals-view">
    <div class="apple-back-bar mb-20 flex-between">
      <button class="apple-back-pill" @click="$router.push('/workspace')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回我的项目</span>
      </button>
      <span class="bar-hint">查阅投稿指南，准备适合目标期刊的写作要求。</span>
    </div>

    <div class="page-header flex-between mb-24">
      <div>
        <div class="page-title">期刊规范</div>
        <div class="page-desc">维护目标期刊的官方投稿指南和风格规范</div>
      </div>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon> 添加期刊
      </el-button>
    </div>

    <!-- 搜索 -->
    <div class="card mb-24">
      <el-input
        v-model="searchQuery"
        placeholder="搜索期刊名称或缩写..."
        @input="debouncedSearch"
        clearable
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <!-- 期刊列表 -->
    <div class="journals-grid">
      <div v-for="journal in journals" :key="journal.id" class="journal-card card">
        <div class="journal-name">{{ journal.name }}</div>
        <div v-if="journal.abbreviation" class="journal-abbr">{{ journal.abbreviation }}</div>
        <div class="journal-tags flex gap-8 mb-8">
          <el-tag v-if="journal.publisher" size="small" type="info">{{ journal.publisher }}</el-tag>
          <el-tag v-if="journal.domain" size="small">{{ journal.domain }}</el-tag>
          <el-tag size="small" type="success">{{ journal.english_variant }} English</el-tag>
        </div>
        <el-descriptions :column="1" size="small" border class="mb-8">
          <el-descriptions-item label="摘要上限">{{ journal.abstract_word_limit || '未设定' }} 词</el-descriptions-item>
          <el-descriptions-item label="引用格式">{{ journal.citation_style || '未设定' }}</el-descriptions-item>
          <el-descriptions-item label="作者指南">
            <a v-if="journal.author_guide_url" :href="journal.author_guide_url" target="_blank" style="color: #4096ff;">
              查看 ↗
            </a>
            <span v-else style="color: #aaa">未录入</span>
          </el-descriptions-item>
        </el-descriptions>
        <el-button size="small" @click="editJournal(journal)">编辑风格规则</el-button>
      </div>
    </div>

    <el-empty v-if="journals.length === 0 && !loading" description="暂无期刊，请添加" />

    <!-- 添加/编辑期刊对话框 -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑期刊' : '添加期刊'" width="680px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="期刊名称" required>
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="缩写">
              <el-input v-model="form.abbreviation" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="出版商">
              <el-input v-model="form.publisher" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学科领域">
              <el-input v-model="form.domain" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="期刊主页 URL">
          <el-input v-model="form.homepage_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="作者指南 URL">
          <el-input v-model="form.author_guide_url" placeholder="https://..." />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="英语规范">
              <el-select v-model="form.english_variant" style="width:100%">
                <el-option label="American English" value="American" />
                <el-option label="British English" value="British" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="摘要字数上限">
              <el-input-number v-model="form.abstract_word_limit" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="引用格式">
              <el-select v-model="form.citation_style" style="width:100%">
                <el-option label="Vancouver" value="Vancouver" />
                <el-option label="APA" value="APA" />
                <el-option label="IEEE" value="IEEE" />
                <el-option label="Chicago" value="Chicago" />
                <el-option label="Harvard" value="Harvard" />
                <el-option label="其他" value="Other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 风格规则 JSON 编辑 -->
        <el-form-item label="风格规则">
          <div style="width:100%">
            <el-input
              v-model="styleRulesJson"
              type="textarea"
              :rows="6"
              placeholder='从官方指南归纳，例如：
{
  "tense": "过去式描述实验，现在式讨论结论",
  "voice": "优先使用主动语态",
  "abbreviations": "首次出现须全称，括号内注明缩写",
  "other": ["避免过长句子", "专业术语需首次解释"]
}'
            />
            <div style="font-size:12px; color:#aaa; margin-top:4px;">
              ⚠ 风格规则应从目标期刊官方作者指南归纳，并记录核验日期
            </div>
          </div>
        </el-form-item>
        <el-form-item label="指南核验日期">
          <el-input v-model="form.guide_verified_date" placeholder="如：2024-10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveJournal" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, ArrowLeft } from '@element-plus/icons-vue'
import { journalsApi } from '../api'

const journals = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const showDialog = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const styleRulesJson = ref('')

const form = ref({
  name: '', abbreviation: '', publisher: '', domain: '',
  homepage_url: '', author_guide_url: '', english_variant: 'American',
  abstract_word_limit: undefined as number | undefined,
  citation_style: '', guide_verified_date: '',
  style_rules: null as any,
})

const resetForm = () => {
  form.value = {
    name: '', abbreviation: '', publisher: '', domain: '',
    homepage_url: '', author_guide_url: '', english_variant: 'American',
    abstract_word_limit: undefined, citation_style: '',
    guide_verified_date: '', style_rules: null,
  }
  styleRulesJson.value = ''
  editingId.value = null
}

const loadJournals = async (search?: string) => {
  loading.value = true
  try {
    journals.value = await journalsApi.list({ search, limit: 100 }) as any[]
  } finally {
    loading.value = false
  }
}

let searchTimeout: any
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => loadJournals(searchQuery.value || undefined), 300)
}

const editJournal = (journal: any) => {
  editingId.value = journal.id
  Object.assign(form.value, journal)
  styleRulesJson.value = journal.style_rules ? JSON.stringify(journal.style_rules, null, 2) : ''
  showDialog.value = true
}

const saveJournal = async () => {
  if (!form.value.name) {
    ElMessage.warning('请填写期刊名称')
    return
  }
  // 解析 JSON 风格规则
  if (styleRulesJson.value) {
    try {
      form.value.style_rules = JSON.parse(styleRulesJson.value)
    } catch {
      ElMessage.error('风格规则 JSON 格式不正确')
      return
    }
  }
  saving.value = true
  try {
    if (editingId.value) {
      const updated = await journalsApi.update(editingId.value, form.value) as any
      const idx = journals.value.findIndex(j => j.id === editingId.value)
      if (idx >= 0) journals.value[idx] = updated
    } else {
      const j = await journalsApi.create(form.value) as any
      journals.value.unshift(j)
    }
    showDialog.value = false
    resetForm()
    ElMessage.success('期刊信息已保存')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => loadJournals())
</script>

<style scoped>
.journals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.journal-card {
  padding: 20px;
}

.journal-name {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.journal-abbr {
  font-size: 13px;
  color: #888;
  margin-bottom: 10px;
}

.journal-tags {
  flex-wrap: wrap;
}
</style>
