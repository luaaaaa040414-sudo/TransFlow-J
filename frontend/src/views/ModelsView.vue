<template>
  <div class="models-view">
    <div class="apple-back-bar mb-20 flex-between">
      <button class="apple-back-pill" @click="$router.push('/workspace')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回我的项目</span>
      </button>
      <span class="bar-hint">为翻译与校对分别设置模型服务。</span>
    </div>

    <div class="page-header flex-between mb-24">
      <div>
        <div class="page-title">模型设置</div>
        <div class="page-desc">直接在网页端配置与管理各厂商 API Key，即存即用，无需手动修改后端文件</div>
      </div>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon> 添加自定义模型
      </el-button>
    </div>

    <!-- 🔑 在线 API Key 配置卡片 -->
    <div class="card mb-24 api-keys-card">
      <div class="flex-between mb-16">
        <div>
          <strong style="font-size: 16px;">🔑 AI 模型提供商 API Key 在线配置</strong>
          <div style="font-size: 13px; color: #888; margin-top: 4px;">
            填入对应厂商的 API Key，点击保存即可直接在网页端使用，系统自动生效并持久化
          </div>
        </div>
        <el-button type="primary" size="large" @click="saveApiKeys" :loading="savingKeys">
          <el-icon><Check /></el-icon> 保存并生效
        </el-button>
      </div>

      <el-form label-width="140px" v-loading="loadingKeys">
        <!-- DeepSeek -->
        <div class="key-provider-box mb-16">
          <div class="provider-title flex-between">
            <div class="flex gap-8" style="align-items: center;">
              <span class="provider-badge deepseek">DeepSeek</span>
              <span class="provider-desc">学术中译英首选推荐，高性价比，中文理解极其精准（支持 V3 与 R1）</span>
            </div>
            <div class="flex gap-8" style="align-items: center;">
              <span v-if="testResults.deepseek" :class="`test-status ${testResults.deepseek.success ? 'success' : 'fail'}`">
                {{ testResults.deepseek.success ? `✓ 连接成功 (${testResults.deepseek.latency_ms}ms)` : `✗ ${testResults.deepseek.error}` }}
              </span>
              <el-button size="small" :loading="testingProvider === 'deepseek'" @click="testProviderConn('deepseek')">
                <el-icon><Connection /></el-icon> 测试连接
              </el-button>
            </div>
          </div>
          <el-row :gutter="16">
            <el-col :span="14">
              <el-form-item label="DeepSeek API Key">
                <el-input
                  v-model="apiKeys.deepseek_api_key"
                  type="password"
                  show-password
                  placeholder="sk-..."
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="Base URL">
                <el-input v-model="apiKeys.deepseek_base_url" placeholder="https://api.deepseek.com/v1" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- OpenAI -->
        <div class="key-provider-box mb-16">
          <div class="provider-title flex-between">
            <div class="flex gap-8" style="align-items: center;">
              <span class="provider-badge openai">OpenAI</span>
              <span class="provider-desc">支持 GPT-4o / o3-mini / GPT-4o-mini 等官方基座模型</span>
            </div>
            <div class="flex gap-8" style="align-items: center;">
              <span v-if="testResults.openai" :class="`test-status ${testResults.openai.success ? 'success' : 'fail'}`">
                {{ testResults.openai.success ? `✓ 连接成功 (${testResults.openai.latency_ms}ms)` : `✗ ${testResults.openai.error}` }}
              </span>
              <el-button size="small" :loading="testingProvider === 'openai'" @click="testProviderConn('openai')">
                <el-icon><Connection /></el-icon> 测试连接
              </el-button>
            </div>
          </div>
          <el-row :gutter="16">
            <el-col :span="14">
              <el-form-item label="OpenAI API Key">
                <el-input
                  v-model="apiKeys.openai_api_key"
                  type="password"
                  show-password
                  placeholder="sk-..."
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="Base URL">
                <el-input v-model="apiKeys.openai_base_url" placeholder="https://api.openai.com/v1" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- Anthropic Claude -->
        <div class="key-provider-box mb-16">
          <div class="provider-title flex-between">
            <div class="flex gap-8" style="align-items: center;">
              <span class="provider-badge anthropic">Anthropic Claude</span>
              <span class="provider-desc">独立第三方 MQM 互审推荐模型（支持 Claude 3.7 / 3.5 Sonnet）</span>
            </div>
            <div class="flex gap-8" style="align-items: center;">
              <span v-if="testResults.anthropic" :class="`test-status ${testResults.anthropic.success ? 'success' : 'fail'}`">
                {{ testResults.anthropic.success ? `✓ 连接成功 (${testResults.anthropic.latency_ms}ms)` : `✗ ${testResults.anthropic.error}` }}
              </span>
              <el-button size="small" :loading="testingProvider === 'anthropic'" @click="testProviderConn('anthropic')">
                <el-icon><Connection /></el-icon> 测试连接
              </el-button>
            </div>
          </div>
          <el-row :gutter="16">
            <el-col :span="14">
              <el-form-item label="Claude API Key">
                <el-input
                  v-model="apiKeys.anthropic_api_key"
                  type="password"
                  show-password
                  placeholder="sk-ant-..."
                  clearable
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 自定义 / 其他 OpenAI 兼容端点 -->
        <div class="key-provider-box">
          <div class="provider-title flex-between">
            <div class="flex gap-8" style="align-items: center;">
              <span class="provider-badge custom">自定义兼容接口</span>
              <span class="provider-desc">支持通义千问、月之暗面、OneAPI / NewAPI 或本地 vLLM 兼容服务</span>
            </div>
            <div class="flex gap-8" style="align-items: center;">
              <span v-if="testResults.custom" :class="`test-status ${testResults.custom.success ? 'success' : 'fail'}`">
                {{ testResults.custom.success ? `✓ 连接成功 (${testResults.custom.latency_ms}ms)` : `✗ ${testResults.custom.error}` }}
              </span>
              <el-button size="small" :loading="testingProvider === 'custom'" @click="testProviderConn('custom')">
                <el-icon><Connection /></el-icon> 测试连接
              </el-button>
            </div>
          </div>
          <el-row :gutter="16">
            <el-col :span="14">
              <el-form-item label="Custom API Key">
                <el-input
                  v-model="apiKeys.custom_api_key"
                  type="password"
                  show-password
                  placeholder="sk-..."
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="Base URL">
                <el-input v-model="apiKeys.custom_base_url" placeholder="https://..." />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-form>
    </div>

    <!-- 已配置模型卡片列表 -->
    <div class="page-header flex-between mb-16">
      <strong style="font-size: 16px;">已启用的模型服务列表</strong>
    </div>

    <div class="models-grid">
      <div v-for="config in configs" :key="config.id" class="model-card card">
        <div class="flex-between mb-16">
          <div>
            <div class="model-name">{{ config.name }}</div>
            <div class="model-id">{{ config.provider }} / {{ config.model_id }}</div>
          </div>
          <el-button size="small" type="danger" link @click="deleteConfig(config)">删除</el-button>
        </div>

        <div class="flex gap-8 mb-8 flex-wrap">
          <el-tag v-if="config.use_for_translation" size="small" type="success">可用于翻译</el-tag>
          <el-tag v-if="config.use_for_proofreading" size="small" type="warning">可用于校对</el-tag>
          <el-tag v-if="config.supports_json_mode" size="small" type="info">JSON 模式</el-tag>
        </div>

        <div v-if="config.capabilities?.length" class="mb-8">
          <div style="font-size:12px; color:#888; margin-bottom:4px">能力说明</div>
          <div class="flex gap-4 flex-wrap">
            <el-tag v-for="cap in config.capabilities" :key="cap" size="small" effect="plain">{{ cap }}</el-tag>
          </div>
        </div>

        <el-descriptions :column="2" size="small">
          <el-descriptions-item v-if="config.context_window" label="上下文">{{ config.context_window?.toLocaleString() }} tokens</el-descriptions-item>
          <el-descriptions-item v-if="config.cost_per_1k_input" label="输入估算">${{ config.cost_per_1k_input }}/1K</el-descriptions-item>
          <el-descriptions-item v-if="config.cost_per_1k_output" label="输出估算">${{ config.cost_per_1k_output }}/1K</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <el-empty v-if="configs.length === 0 && !loading" description="暂无模型配置，请点击下方快速添加">
      <el-button type="primary" @click="showDialog = true">添加第一个模型</el-button>
    </el-empty>

    <!-- 预设模型快速添加 -->
    <div class="card mt-24">
      <strong style="font-size: 15px;">⚡ 一键快速添加预设学术模型</strong>
      <div style="font-size: 13px; color: #888; margin: 4px 0 12px 0;">
        包含针对学术翻译与独立校对调优的常用主流模型
      </div>
      <div class="flex gap-8 flex-wrap">
        <el-button v-for="preset in PRESETS" :key="preset.name" @click="addPreset(preset)">
          + {{ preset.name }}
        </el-button>
      </div>
    </div>

    <!-- 添加自定义模型对话框 -->
    <el-dialog v-model="showDialog" title="添加自定义模型" width="560px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="显示名称" required>
          <el-input v-model="form.name" placeholder="如：DeepSeek-V3 快速学术翻译" />
        </el-form-item>
        <el-form-item label="提供商" required>
          <el-select v-model="form.provider" style="width:100%">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="自定义 / 其他兼容服务" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型 ID" required>
          <el-input v-model="form.model_id" placeholder="如：deepseek-chat / gpt-4o / claude-3-5-sonnet-20241022" />
        </el-form-item>
        <el-form-item label="API 端点 URL">
          <el-input v-model="form.api_base_url" placeholder="默认使用提供商官方端点，可留空" />
        </el-form-item>
        <el-form-item label="上下文窗口">
          <el-input-number v-model="form.context_window" :min="0" :step="1000" placeholder="tokens" style="width:100%" />
        </el-form-item>
        <el-form-item label="能力标签">
          <el-select v-model="form.capabilities" multiple filterable allow-create style="width:100%">
            <el-option label="中文理解强" value="中文理解强" />
            <el-option label="长文处理" value="长文处理" />
            <el-option label="结构化输出" value="结构化输出" />
            <el-option label="推理能力强" value="推理能力强" />
            <el-option label="学术写作" value="学术写作" />
            <el-option label="快速响应" value="快速响应" />
          </el-select>
        </el-form-item>
        <el-form-item label="用途配置">
          <el-checkbox v-model="form.use_for_translation">用于翻译</el-checkbox>
          <el-checkbox v-model="form.use_for_proofreading">用于独立校对</el-checkbox>
          <el-checkbox v-model="form.supports_json_mode">支持结构化 JSON 模式</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存模型</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check, Connection, ArrowLeft } from '@element-plus/icons-vue'
import { modelsApi } from '../api'

const configs = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)

// API Key 在线配置状态
const loadingKeys = ref(false)
const savingKeys = ref(false)
const testingProvider = ref<string | null>(null)
const testResults = ref<Record<string, { success: boolean; latency_ms?: number; error?: string }>>({})

const apiKeys = ref({
  openai_api_key: '',
  openai_base_url: 'https://api.openai.com/v1',
  deepseek_api_key: '',
  deepseek_base_url: 'https://api.deepseek.com/v1',
  anthropic_api_key: '',
  custom_api_key: '',
  custom_base_url: '',
})

const PRESETS = [
  { name: 'DeepSeek-R1 (最新深度推理旗舰)', provider: 'deepseek', model_id: 'deepseek-reasoner', context_window: 128000, capabilities: ['长链深度思考(CoT)', '极强数理逻辑', '学术论文严密审查', '高性价比'], cost_per_1k_input: 0.00055, cost_per_1k_output: 0.00219, supports_json_mode: true, use_for_translation: true, use_for_proofreading: true },
  { name: 'DeepSeek-V3 (学术中译英通用主力)', provider: 'deepseek', model_id: 'deepseek-chat', context_window: 128000, capabilities: ['中文理解强', '极速响应', '高性价比', '期刊风格适配'], cost_per_1k_input: 0.00014, cost_per_1k_output: 0.00028, supports_json_mode: true, use_for_translation: true, use_for_proofreading: true },
  { name: 'Claude 3.7 Sonnet (2025最新混合推理)', provider: 'anthropic', model_id: 'claude-3-7-sonnet-20250219', context_window: 200000, capabilities: ['混合思考推理', '顶尖科技学术校对', '细致文风规范'], cost_per_1k_input: 0.003, cost_per_1k_output: 0.015, supports_json_mode: false, use_for_translation: true, use_for_proofreading: true },
  { name: 'Claude 3.5 Sonnet (经典独立校对评测)', provider: 'anthropic', model_id: 'claude-3-5-sonnet-20241022', context_window: 200000, capabilities: ['长文处理', '推理能力强', '细微语感与语法检查'], cost_per_1k_input: 0.003, cost_per_1k_output: 0.015, supports_json_mode: false, use_for_translation: false, use_for_proofreading: true },
  { name: 'GPT-4o (通用多模态基座)', provider: 'openai', model_id: 'gpt-4o', context_window: 128000, capabilities: ['长文处理', '结构化输出', '学术写作'], cost_per_1k_input: 0.0025, cost_per_1k_output: 0.01, supports_json_mode: true, use_for_translation: true, use_for_proofreading: true },
  { name: 'o3-mini (理工逻辑强推理基座)', provider: 'openai', model_id: 'o3-mini', context_window: 200000, capabilities: ['STEM强推理', '逻辑一致性检验', '高准确度'], cost_per_1k_input: 0.0011, cost_per_1k_output: 0.0044, supports_json_mode: true, use_for_translation: true, use_for_proofreading: true },
]

const defaultForm = () => ({
  name: '', provider: 'deepseek', model_id: '', api_base_url: '',
  context_window: undefined as number | undefined,
  capabilities: [] as string[],
  cost_per_1k_input: undefined as number | undefined,
  cost_per_1k_output: undefined as number | undefined,
  supports_json_mode: true,
  use_for_translation: true,
  use_for_proofreading: true,
})

const form = ref(defaultForm())

const loadConfigs = async () => {
  loading.value = true
  try {
    configs.value = await modelsApi.list() as any[]
  } finally {
    loading.value = false
  }
}

const loadApiKeys = async () => {
  loadingKeys.value = true
  try {
    const keys = await modelsApi.getKeys() as any
    if (keys) {
      Object.assign(apiKeys.value, keys)
    }
  } catch (e: any) {
    console.error('加载 API Keys 失败', e)
  } finally {
    loadingKeys.value = false
  }
}

const saveApiKeys = async () => {
  savingKeys.value = true
  try {
    await modelsApi.saveKeys(apiKeys.value)
    ElMessage.success('API Keys 已在线保存并即时生效！')
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    savingKeys.value = false
  }
}

const testProviderConn = async (provider: string) => {
  testingProvider.value = provider
  try {
    let apiKey = ''
    let baseUrl = ''
    let model = ''

    if (provider === 'deepseek') {
      apiKey = apiKeys.value.deepseek_api_key
      baseUrl = apiKeys.value.deepseek_base_url
      model = 'deepseek-chat'
    } else if (provider === 'openai') {
      apiKey = apiKeys.value.openai_api_key
      baseUrl = apiKeys.value.openai_base_url
      model = 'gpt-4o'
    } else if (provider === 'anthropic') {
      apiKey = apiKeys.value.anthropic_api_key
      model = 'claude-3-5-sonnet-20241022'
    } else if (provider === 'custom') {
      apiKey = apiKeys.value.custom_api_key
      baseUrl = apiKeys.value.custom_base_url
      model = 'gpt-3.5-turbo'
    }

    const res = await modelsApi.testProvider({
      provider,
      api_key: apiKey,
      base_url: baseUrl,
      model,
    }) as any

    testResults.value[provider] = {
      success: res.success,
      latency_ms: res.latency_ms,
      error: res.error,
    }

    if (res.success) {
      ElMessage.success(`${provider.toUpperCase()} 连接成功！响应延迟 ${res.latency_ms} ms`)
    } else {
      ElMessage.error(`${provider.toUpperCase()} 连接失败：${res.error}`)
    }
  } catch (e: any) {
    testResults.value[provider] = {
      success: false,
      error: e.message,
    }
    ElMessage.error(`测试失败：${e.message}`)
  } finally {
    testingProvider.value = null
  }
}

const saveConfig = async () => {
  if (!form.value.name || !form.value.model_id) {
    ElMessage.warning('请填写显示名称和模型 ID')
    return
  }
  saving.value = true
  try {
    const config = await modelsApi.create(form.value) as any
    configs.value.unshift(config)
    showDialog.value = false
    form.value = defaultForm()
    ElMessage.success('模型配置已保存')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

const addPreset = async (preset: any) => {
  saving.value = true
  try {
    const config = await modelsApi.create({ name: preset.name, ...preset }) as any
    configs.value.unshift(config)
    ElMessage.success(`已添加预设：${preset.name}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

const deleteConfig = async (config: any) => {
  await ElMessageBox.confirm(`删除模型配置「${config.name}」？`, '确认', { type: 'warning' })
  try {
    await modelsApi.delete(config.id)
    configs.value = configs.value.filter(c => c.id !== config.id)
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(() => {
  loadConfigs()
  loadApiKeys()
})
</script>

<style scoped>
.api-keys-card {
  border: 1px solid #cce5ff;
  background: #fcfdff;
}

.key-provider-box {
  background: #ffffff;
  border: 1px solid #e8edf3;
  border-radius: 8px;
  padding: 16px 20px 8px 20px;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.provider-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.provider-badge.deepseek { background: #0066ff; }
.provider-badge.openai { background: #10a37f; }
.provider-badge.anthropic { background: #d97706; }
.provider-badge.custom { background: #6b7280; }

.provider-desc {
  font-size: 12px;
  color: #888;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.model-card { padding: 20px; }
.model-name { font-size: 16px; font-weight: 700; color: #1a1a2e; }
.model-id { font-size: 13px; color: #888; font-family: monospace; }
.mt-24 { margin-top: 24px; }
.flex-wrap { flex-wrap: wrap; }
.gap-4 { gap: 4px; }

.test-status {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
}
.test-status.success {
  background: #f6ffed;
  color: #389e0d;
  border: 1px solid #b7eb8f;
}
.test-status.fail {
  background: #fff2f0;
  color: #cf1322;
  border: 1px solid #ffccc7;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
