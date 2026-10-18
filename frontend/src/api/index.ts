/**
 * API 服务层 - 统一封装所有后端请求
 */
import axios from 'axios'

// 默认走同源相对路径 /api/v1，由 Vite 的 proxy 转发到本机 8000 端口的 FastAPI。
// 这样局域网 / 内网穿透访问时，请求打的是「访客看到的那个域名」，不会去连访客自己的 127.0.0.1。
// 需要指向别的后端时，用 VITE_API_BASE_URL 覆盖（例如 http://192.168.1.10:8000/api/v1）。
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 120s，因为翻译可能较慢
  headers: { 'Content-Type': 'application/json' },
})

// 统一错误处理
apiInstance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

const http = {
  get: (url: string, config?: any): Promise<any> => apiInstance.get(url, config),
  post: (url: string, data?: any, config?: any): Promise<any> => apiInstance.post(url, data, config),
  put: (url: string, data?: any, config?: any): Promise<any> => apiInstance.put(url, data, config),
  delete: (url: string, config?: any): Promise<any> => apiInstance.delete(url, config),
}

// ============================================================
// 项目 API
// ============================================================
export const projectsApi = {
  list: (): Promise<any> => http.get('/projects'),
  create: (data: any): Promise<any> => http.post('/projects', data),
  get: (id: number): Promise<any> => http.get(`/projects/${id}`),
  update: (id: number, data: any): Promise<any> => http.put(`/projects/${id}`, data),
  delete: (id: number): Promise<any> => http.delete(`/projects/${id}`),
  stats: (id: number): Promise<any> => http.get(`/projects/${id}/stats`),
}

// ============================================================
// 文档 API
// ============================================================
export const documentsApi = {
  upload: (projectId: number, file: File, onProgress?: (p: number) => void): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    return http.post(`/documents/upload/${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: any) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
      },
    })
  },
  get: (documentId: number): Promise<any> => http.get(`/documents/${documentId}`),
  listByProject: (projectId: number): Promise<any> => http.get(`/documents/project/${projectId}`),
}

// ============================================================
// 翻译 API
// ============================================================
export const translationApi = {
  listSegments: (projectId: number, params?: Record<string, any>): Promise<any> =>
    http.get(`/translation/segments/${projectId}`, { params }),
  getSegment: (segmentDbId: number): Promise<any> => http.get(`/translation/segment/${segmentDbId}`),
  updateSegment: (segmentDbId: number, data: any): Promise<any> =>
    http.put(`/translation/segment/${segmentDbId}`, data),
  translateSegment: (segmentDbId: number, provider: string, model: string): Promise<any> =>
    http.post(`/translation/translate/segment/${segmentDbId}`, null, {
      params: { provider, model },
    }),
  translateProject: (projectId: number, data?: any): Promise<any> =>
    http.post(`/translation/translate/project/${projectId}`, data || {}),
  testConnection: (provider: string, model: string): Promise<any> =>
    http.post('/translation/test-connection', null, { params: { provider, model } }),
}

// ============================================================
// 术语 API
// ============================================================
export const terminologyApi = {
  list: (projectId: number, status?: string): Promise<any> =>
    http.get(`/terminology/project/${projectId}`, { params: { status } }),
  create: (projectId: number, data: any): Promise<any> =>
    http.post(`/terminology/project/${projectId}`, data),
  get: (termId: number): Promise<any> => http.get(`/terminology/${termId}`),
  update: (termId: number, data: any): Promise<any> => http.put(`/terminology/${termId}`, data),
  delete: (termId: number): Promise<any> => http.delete(`/terminology/${termId}`),
  confirm: (termId: number, translation: string): Promise<any> =>
    http.post(`/terminology/${termId}/confirm`, null, {
      params: { confirmed_translation: translation },
    }),
  autoResearch: (termId: number): Promise<any> =>
    http.post(`/terminology/${termId}/auto-research`),
  addEvidence: (termId: number, data: any): Promise<any> =>
    http.post(`/terminology/${termId}/evidence`, data),
  listEvidence: (termId: number): Promise<any> =>
    http.get(`/terminology/${termId}/evidence`),
  verifyEvidence: (evidenceId: number, isValid: boolean): Promise<any> =>
    http.put(`/terminology/evidence/${evidenceId}/verify`, null, {
      params: { is_valid: isValid },
    }),
}

// ============================================================
// 期刊 API
// ============================================================
export const journalsApi = {
  list: (params?: Record<string, any>): Promise<any> => http.get('/journals', { params }),
  create: (data: any): Promise<any> => http.post('/journals', data),
  get: (id: number): Promise<any> => http.get(`/journals/${id}`),
  update: (id: number, data: any): Promise<any> => http.put(`/journals/${id}`, data),
}

// ============================================================
// 模型配置 API
// ============================================================
export const modelsApi = {
  list: (useFor?: string): Promise<any> => http.get('/models', { params: { use_for: useFor } }),
  create: (data: any): Promise<any> => http.post('/models', data),
  delete: (id: number): Promise<any> => http.delete(`/models/${id}`),
  getKeys: (): Promise<any> => http.get('/models/settings/keys'),
  saveKeys: (data: any): Promise<any> => http.post('/models/settings/keys', data),
  testProvider: (data: { provider: string; api_key?: string; base_url?: string; model?: string }): Promise<any> =>
    http.post('/models/test-provider', data),
}

// ============================================================
// 校对 API
// ============================================================
export const proofreadingApi = {
  proofreadSegment: (segmentDbId: number, provider: string, model: string): Promise<any> =>
    http.post(`/proofreading/segment/${segmentDbId}`, null, {
      params: { provider, model },
    }),
  listIssues: (projectId: number, params?: Record<string, any>): Promise<any> =>
    http.get(`/proofreading/issues/${projectId}`, { params }),
  decideIssue: (issueId: number, data: any): Promise<any> =>
    http.put(`/proofreading/issue/${issueId}/decide`, data),
}

// ============================================================
// 报告 API
// ============================================================
export const reportsApi = {
  generate: (projectId: number): Promise<any> => http.post(`/reports/generate/${projectId}`),
  list: (projectId: number): Promise<any> => http.get(`/reports/${projectId}`),
  get: (reportId: number): Promise<any> => http.get(`/reports/detail/${reportId}`),
}

// ============================================================
// 导出 API
// ============================================================
export const exportApi = {
  englishDocxUrl: (projectId: number) => `${BASE_URL}/export/english-docx/${projectId}`,
  bilingualDocxUrl: (projectId: number) => `${BASE_URL}/export/bilingual-docx/${projectId}`,
  terminologyXlsxUrl: (projectId: number) => `${BASE_URL}/export/terminology-xlsx/${projectId}`,
  mqmXlsxUrl: (projectId: number) => `${BASE_URL}/export/mqm-xlsx/${projectId}`,
  archiveZipUrl: (projectId: number) => `${BASE_URL}/export/archive-zip/${projectId}`,
}

export default apiInstance
