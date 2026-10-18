#!/usr/bin/env node
/**
 * 内网穿透：把本地正在运行的前端服务暴露成一个公网地址，
 * 发给不在同一局域网的同事，任何网络都能打开。
 *
 * 用法：
 *   node scripts/tunnel.mjs            # 自动探测前端端口（5173→5176）
 *   node scripts/tunnel.mjs 5174       # 手动指定端口
 *
 * 前置：需要 cloudflared（一次性安装）
 *   winget install Cloudflare.cloudflared
 *   或从 https://github.com/cloudflare/cloudflared/releases 下载 exe 放进 PATH
 *
 * 原理：cloudflared 的「快速隧道」不需要注册账号，直接生成一个
 *       https://xxxx.trycloudflare.com 临时地址，关掉就失效。
 *       后端接口由前端 /api 代理转发，所以只需穿透前端一个端口。
 */
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const CANDIDATES = [5173, 5174, 5175, 5176]

/** winget 安装后的固定位置；找不到就交给 PATH 解析 */
function resolveCloudflared() {
  const fixed = [
    'C:\\Program Files (x86)\\cloudflared\\cloudflared.exe',
    'C:\\Program Files\\cloudflared\\cloudflared.exe',
  ]
  for (const p of fixed) {
    if (fs.existsSync(p)) return p
  }
  return 'cloudflared'
}

function checkPort(host, port, timeout = 1200) {
  return new Promise((resolve) => {
    const s = net.connect({ host, port })
    const finish = (ok) => { try { s.destroy() } catch {} ; resolve(ok) }
    s.setTimeout(timeout)
    s.once('connect', () => finish(true))
    s.once('timeout', () => finish(false))
    s.once('error', () => finish(false))
  })
}

async function detectPort() {
  const arg = process.argv[2]
  if (arg) return Number(arg)
  for (const p of CANDIDATES) {
    if (await checkPort('127.0.0.1', p)) return p
  }
  return null
}

const port = await detectPort()

if (!port) {
  console.error('\n[X] 没检测到正在运行的前端服务。')
  console.error('    请先在另一个终端窗口运行：cd frontend && npm run dev')
  console.error('    （那个窗口要一直开着）\n')
  process.exit(1)
}

console.log(`\n=== 内网穿透：本地 :${port} → 公网 ===`)
console.log('正在建立隧道，请稍等几秒…\n')

// 用 127.0.0.1 而非 localhost：避免解析到 IPv6 回环 [::1]，
// 而 Vite 只监听 IPv4（0.0.0.0），连 [::1] 会 connection refused。
// 不用 shell：直接用 exe 路径启动，避免 "C:\Program Files (x86)\..." 里的空格被拆开
const child = spawn(resolveCloudflared(), ['tunnel', '--url', `http://127.0.0.1:${port}`, '--no-autoupdate'], {
  stdio: ['ignore', 'pipe', 'pipe'],
})

let printed = false
function handle(buf) {
  const text = buf.toString()
  process.stderr.write(text)
  const m = text.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/)
  if (m && !printed) {
    printed = true
    const url = m[0]
    // 同时落盘一份，方便随时查看「当前」地址（旧地址会失效，别记混）
    try {
      fs.writeFileSync(
        path.join(PROJECT_ROOT, 'TUNNEL-URL.txt'),
        `${url}\n生成时间：${new Date().toLocaleString('zh-CN')}\n本地端口：${port}\n`,
        'utf8',
      )
    } catch {}
    console.log('\n' + '='.repeat(58))
    console.log('  把这个公网地址发给同事（他们用什么网络都能打开）：')
    console.log('  ' + url)
    console.log('='.repeat(58))
    console.log('\n  （该地址已同时写入项目根目录的 TUNNEL-URL.txt，方便随时查看）')
    console.log('\n  提示：')
    console.log('   - 保持本窗口开着；关掉窗口隧道就断了')
    console.log('   - 后端接口由前端 /api 自动代理，不用另外穿透')
    console.log('   - 首次访问可能出现 Cloudflare 提示页，点继续即可')
    console.log('   - 这个地址是临时的，每次重启都会变')
    console.log('')
    console.log(`   ⚠ 本隧道固定指向本地 :${port}。若你重启了 vite 导致端口变化，`)
    console.log('     隧道会返回 502 Bad Gateway —— 关掉本窗口重新运行一次即可。\n')
  }
}

child.stdout.on('data', handle)
child.stderr.on('data', handle)
child.on('error', (e) => {
  console.error('\n[X] 启动 cloudflared 失败：' + e.message)
  console.error('    请确认已安装：winget install Cloudflare.cloudflared\n')
  process.exit(1)
})
child.on('exit', (code) => {
  console.log(`\n隧道已关闭（退出码 ${code}）。\n`)
  process.exit(code ?? 0)
})
