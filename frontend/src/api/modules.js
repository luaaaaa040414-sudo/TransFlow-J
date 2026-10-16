import request from './request'

// 信源分级
export const fetchSourceTiers = () => request.get('/sources/tiers')
export const classifySource = (url) => request.post('/sources/classify', { url })

// 译前准备：术语查证
export const analyzeTerm = (term, context) => request.post('/term/analyze', { term, context })
// 译前准备：直取一级源（术语在线）权威英文译名，供页面直接显示
export const fetchAuthority = (term) => request.post('/term/authority', { term })

// 模型池
export const fetchModels = () => request.get('/models')

// 期刊风格翻译（成段 / 整篇）
export const styleTranslate = (payload) => request.post('/style/translate', payload)

// 期刊风格库
export const fetchDomains = () => request.get('/profiles/domains')
export const fetchDomainDetail = (domain) => request.get(`/profiles/domains/${domain}`)
// 全库期刊平铺清单（供流水线总览的目标期刊下拉选择）
export const fetchAllJournals = () => request.get('/journals')

// 流水线
export const runPipeline = (payload) => request.post('/pipeline/run', payload)
export const fetchPipelineStatus = (jobId) => request.get(`/pipeline/status/${jobId}`)
