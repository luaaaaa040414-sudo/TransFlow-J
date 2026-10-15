import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发服务器默认端口 5173，接口统一走 /api 代理到 Java 后端。
// 后端地址默认 8080（IDEA 里跑的那个）；如需指向其他端口，启动前设置环境变量：
//   Windows: set VITE_API_TARGET=http://127.0.0.1:18080 && npm run dev
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true
      }
    }
  }
})
