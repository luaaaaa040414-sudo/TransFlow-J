import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发服务器配置
//   host: '0.0.0.0'  —— 监听所有网卡，局域网内其他同学可用 http://<你的IP>:5173 打开，
//                       不要用 localhost，那样只有本机能访问。
//   /api 代理到 Java 后端（服务端转发，所以这里写 127.0.0.1 是正确的，
//   指「本机上跑的后端」；浏览器看到的是同源请求，不会有跨域问题）。
//   若后端跑在另一台机器：启动前设置环境变量 VITE_API_TARGET=http://<后端IP>:8080
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    // 允许通过任意域名访问。内网穿透（ngrok / Cloudflare Tunnel）会把本地服务
    // 映射成一个公网域名，而 Vite 默认只接受 localhost 与 IP 的 Host 头，
    // 用域名访问会被拒（返回 "Blocked request. This host is not allowed."）。
    allowedHosts: true,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 4173
  }
})
