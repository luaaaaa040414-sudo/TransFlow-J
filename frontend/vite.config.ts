import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// ============================================================
// 后端是 Python FastAPI（backend/app），监听 127.0.0.1:8000，接口前缀 /api/v1
//
// 前端一律用相对路径 /api/v1 请求（见 src/api/index.ts），由这里的 proxy 转发。
// 不要在前端写死 http://127.0.0.1:8000 —— 那样同事通过局域网或内网穿透打开页面时，
// 请求会打到「他自己电脑的 127.0.0.1」，必然连不上；而且 https 页面请求 http 会被浏览器拦截。
//
// 后端跑在另一台机器时：启动前设 VITE_API_TARGET=http://<后端IP>:8000
// ============================================================
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'

const proxy = {
  '/api': {
    target: API_TARGET,
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [vue()],
  server: {
    // 监听所有网卡，局域网内其他同学可用 http://<你的IP>:5173 打开
    host: '0.0.0.0',
    port: 5173,
    // 端口被占用直接报错，不静默换端口（换了端口内网穿透会指向空端口）
    strictPort: true,
    // 允许通过任意域名访问。Vite 默认只接受 localhost / IP 的 Host 头，
    // 用 ngrok 域名访问会被拒（Blocked request. This host is not allowed.）
    allowedHosts: true,
    proxy,
  },
  // 打包预览：给同学看效果时用这个（npm run share），比 dev server 快一个数量级
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: true,
    allowedHosts: true,
    // preview 不会自动沿用 server.proxy，必须显式写
    proxy,
  },
})
