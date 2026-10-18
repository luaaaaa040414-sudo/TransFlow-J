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
    // strictPort: true —— 端口被占用时直接报错，而不是「悄悄换成 5174」。
    // 这样做内网穿透时端口恒定，隧道不用重跑；
    // 否则一旦自动换端口，已建立的隧道会指向空端口，同事那边报 502。
    strictPort: true,
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
  // 打包预览（npm run build && vite preview）
  //   给同事分享时用这个，不要用 dev server：
  //   dev 模式每个 .vue 都单独请求，经内网穿透中转后首屏要 20~30 秒，看起来像白屏；
  //   打包后只有几个文件，公网几秒就能打开。
  preview: {
    host: '0.0.0.0',
    port: 4173,
    // 端口被占用直接报错，避免隧道指向空端口
    strictPort: true,
    // 同 server.allowedHosts：ngrok / Cloudflare 的域名必须放行
    allowedHosts: true,
    // preview 默认继承 server.proxy，这里显式写一遍，避免升级 Vite 后行为变化
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true
      }
    }
  }
})
