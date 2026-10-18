/**
 * TransFlow-J 内网穿透（ngrok 固定域名版）
 *
 * 与 tunnel.mjs（cloudflared 快速隧道）的区别：
 *   - cloudflared 快速隧道：免注册，但每次重启地址都变
 *   - ngrok 固定域名：需注册账号，但地址永久不变
 *
 * 用法（仓库根目录）：
 *   node scripts/ngrok.mjs
 *   node scripts/ngrok.mjs 5173        # 指定端口
 *
 * 前置条件：
 *   1. tools/ngrok.yml 里已写入 authtoken（见 README）
 *   2. 账号已创建 dev domain（ngrok 免费版给 1 个，永久有效）
 *
 * 注意两个坑（都已在本脚本内处理）：
 *   1. ngrok 检测到 http_proxy 环境变量会要求付费计划（ERR_NGROK_9009）
 *      → 启动时必须清掉所有代理环境变量
 *   2. 免费版不能自定义子域名（ERR_NGROK_313）
 *      → 不要传 --url/--domain，ngrok 会自动使用账号绑定的那个 dev domain
 */
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const NGROK_CONFIG = path.join(ROOT, 'tools', 'ngrok.yml')
const CANDIDATES = [5173, 5174, 5175, 5176]

function probe(port) {
  return new Promise((resolve) => {
    const s = net.connect({ host: '127.0.0.1', port }, () => {
      s.destroy()
      resolve(true)
    })
    s.on('error', () => resolve(false))
    s.setTimeout(800, () => {
      s.destroy()
      resolve(false)
    })
  })
}

async function findPort() {
  const arg = process.argv[2]
  if (arg && /^\d+$/.test(arg)) {
    if (await probe(Number(arg))) return Number(arg)
    console.error(`✗ 端口 ${arg} 没有服务在监听，请先启动前端`)
    process.exit(1)
  }
  for (const p of CANDIDATES) {
    if (await probe(p)) return p
  }
  console.error('✗ 找不到正在运行的前端服务（已试过 5173~5176）')
  console.error('  请先在 frontend 目录运行 npm run dev')
  process.exit(1)
}

function resolveNgrok() {
  const local = path.join(ROOT, 'tools', 'ngrok.exe')
  if (fs.existsSync(local)) return local
  // winget 安装的真实二进制位置（Links 目录下的别名可能是 0 字节空文件）
  const wingetPkg = path.join(
    process.env.LOCALAPPDATA || '',
    'Microsoft', 'WinGet', 'Packages',
  )
  if (fs.existsSync(wingetPkg)) {
    for (const dir of fs.readdirSync(wingetPkg)) {
      if (!/^Ngrok\.Ngrok_/i.test(dir)) continue
      const exe = path.join(wingetPkg, dir, 'ngrok.exe')
      if (fs.existsSync(exe) && fs.statSync(exe).size > 1024 * 1024) return exe
    }
  }
  return 'ngrok'
}

// 关键：清掉代理环境变量，否则 ngrok 报 ERR_NGROK_9009（代理是付费功能）
function cleanEnv() {
  const env = { ...process.env }
  for (const k of ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy', 'no_proxy', 'NO_PROXY']) {
    delete env[k]
  }
  return env
}

const port = await findPort()
const exe = resolveNgrok()

if (!fs.existsSync(NGROK_CONFIG)) {
  console.error(`✗ 找不到 ngrok 配置：${NGROK_CONFIG}`)
  console.error('  请先创建该文件并写入：')
  console.error('    version: "2"')
  console.error('    authtoken: <你的 authtoken>')
  process.exit(1)
}

console.log(`\n=== ngrok 固定域名隧道：本地 :${port} → 公网 ===\n`)

// 不传 --url：免费版不允许自定义子域名，ngrok 会自动用账号绑定的 dev domain
const child = spawn(exe, ['http', String(port), '--config', NGROK_CONFIG, '--log=stdout'], {
  stdio: ['ignore', 'pipe', 'pipe'],
  env: cleanEnv(),
})

let printed = false

function handle(text) {
  // 从日志里抓取实际分配的地址
  const m = text.match(/https:\/\/[a-z0-9-]+\.ngrok-free\.[a-z]+/)
  if (m && !printed) {
    printed = true
    const url = m[0]
    console.log('='.repeat(58))
    console.log('  固定公网地址（重启后依然是这个）：')
    console.log('  ' + url)
    console.log('='.repeat(58))
    console.log('  本地端口：' + port)
    console.log('  保持本窗口开着，关掉就断开')
    console.log('  后端接口由前端 /api 自动代理，不用另外穿透\n')
    try {
      fs.writeFileSync(
        path.join(ROOT, 'TUNNEL-URL.txt'),
        `${url}\n生成时间：${new Date().toLocaleString('zh-CN')}\n本地端口：${port}\n方式：ngrok 固定域名\n`,
        'utf8',
      )
    } catch {}
    return
  }
  if (/ERR_NGROK_9009/.test(text)) {
    console.error('\n✗ 代理环境变量未清干净（ERR_NGROK_9009）')
  } else if (/ERR_NGROK_313/.test(text)) {
    console.error('\n✗ 免费版不能自定义子域名，不要传 --url / --domain')
  } else if (/ERR_NGROK_4018/.test(text)) {
    console.error('\n✗ 未认证：authtoken 无效或未写入 tools/ngrok.yml')
  }
}

child.stdout.on('data', (d) => handle(d.toString()))
child.stderr.on('data', (d) => handle(d.toString()))

child.on('exit', (code) => {
  if (!printed) console.error(`\n隧道进程退出（code=${code}），请检查上方报错`)
  else console.log('\n隧道已断开。')
})

process.on('SIGINT', () => {
  child.kill()
  process.exit(0)
})
