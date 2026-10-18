/**
 * TransFlow-J 一键分享（打包预览 + ngrok 固定域名）
 *
 * 为什么不用 dev server 分享：
 *   Vite dev server 是按模块单独请求的（几百个 .vue 与依赖），每个都要经内网穿透中转，
 *   公网首屏实测要 20~30 秒，看起来像白屏。打包后只有几个文件，几秒就能打开。
 *
 * 用法（仓库根目录）：
 *   node scripts/share.mjs               # 打包 → 起 preview(4173) → 起 ngrok（手动更新代码后跑这个）
 *   node scripts/share.mjs --serve-only  # 跳过打包，只起 preview + ngrok（开机自启任务用这个）
 *
 * 产物：
 *   - 预览服务：http://127.0.0.1:4173（局域网同事也可用 http://<你的IP>:4173）
 *   - 公网地址：https://submitter-stoneware-upstage.ngrok-free.dev（固定，重启不变）
 *   - 日志：tools/share.log（后台运行时排查用）
 *
 * 注意：
 *   1. ngrok 检测到 http_proxy/https_proxy 会要求付费计划（ERR_NGROK_9009）→ 启动前清掉代理变量
 *   2. 免费版不能自定义子域名（ERR_NGROK_313）→ 不传 --url/--domain
 *   3. 免费版新访客第一次会看到 ngrok 警告页，点一次 "Visit Site" 即可
 */
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const FRONTEND = path.join(ROOT, 'frontend')
const VITE_BIN = path.join(FRONTEND, 'node_modules', 'vite', 'bin', 'vite.js')
const NGROK_CONFIG = path.join(ROOT, 'tools', 'ngrok.yml')
const LOG_FILE = path.join(ROOT, 'tools', 'share.log')
const PORT = 4173
const SERVE_ONLY = process.argv.includes('--serve-only')

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function log(msg) {
  const line = `[${new Date().toLocaleString('zh-CN')}] ${msg}`
  console.log(line)
  try {
    fs.appendFileSync(LOG_FILE, line + '\n', 'utf8')
  } catch {}
}

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

function runNode(args, cwd, tag) {
  return new Promise((resolve, reject) => {
    const p = spawn(process.execPath, args, { cwd, stdio: ['ignore', 'pipe', 'pipe'] })
    p.stdout.on('data', (d) => log(`[${tag}] ${d.toString().trim()}`))
    p.stderr.on('data', (d) => log(`[${tag}:err] ${d.toString().trim()}`))
    p.on('exit', (code) => (code === 0 ? resolve() : reject(new Error(`${tag} 退出 code=${code}`))))
  })
}

async function build() {
  if (!fs.existsSync(VITE_BIN)) {
    throw new Error(`找不到 vite：${VITE_BIN}\n请先在 frontend 目录执行 npm install`)
  }
  log('开始打包前端（vite build）…')
  await runNode([VITE_BIN, 'build'], FRONTEND, 'build')
  log('打包完成')
}

// 源码是否比 dist 新（决定 --serve-only 时要不要补一次打包）
function newestMtime(target) {
  let max = 0
  const walk = (p) => {
    const st = fs.statSync(p)
    if (st.isDirectory()) {
      for (const name of fs.readdirSync(p)) walk(path.join(p, name))
    } else {
      max = Math.max(max, st.mtimeMs)
    }
  }
  if (fs.existsSync(target)) walk(target)
  return max
}

function needsBuild() {
  const distIndex = path.join(FRONTEND, 'dist', 'index.html')
  if (!fs.existsSync(distIndex)) return 'dist 不存在'
  const distTime = fs.statSync(distIndex).mtimeMs
  const srcTime = Math.max(
    newestMtime(path.join(FRONTEND, 'src')),
    newestMtime(path.join(FRONTEND, 'vite.config.ts')),
    newestMtime(path.join(FRONTEND, 'vite.config.js')),
    newestMtime(path.join(FRONTEND, 'index.html')),
  )
  if (srcTime > distTime) return '源码比 dist 新'
  return null
}

// 后端：Python FastAPI（backend/app），监听 8000，接口前缀 /api/v1
// 没在跑就顺手拉起来，这样开机自启一个任务就把前后端都带起来
async function ensureBackend() {
  const BACKEND_PORT = 8000
  if (await probe(BACKEND_PORT)) {
    log(`:${BACKEND_PORT} 后端已在运行，直接复用`)
    return null
  }
  const py = path.join(ROOT, 'backend', '.venv-win', 'Scripts', 'python.exe')
  if (!fs.existsSync(py)) {
    log(`⚠ 没找到后端虚拟环境 ${py}`)
    log('  首次使用请先执行：')
    log('  cd backend && python -m venv .venv-win && .venv-win\\Scripts\\pip install -r requirements.txt')
    return null
  }
  log('启动 FastAPI 后端 …')
  const p = spawn(py, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
    cwd: path.join(ROOT, 'backend'),
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  p.stdout.on('data', (d) => log('[backend] ' + d.toString().trim()))
  p.stderr.on('data', (d) => log('[backend] ' + d.toString().trim()))
  for (let i = 0; i < 80; i++) {
    await sleep(500)
    if (await probe(BACKEND_PORT)) {
      log(`后端就绪：http://127.0.0.1:${BACKEND_PORT}/docs`)
      return p
    }
    if (p.exitCode !== null) {
      log(`⚠ 后端进程退出（code=${p.exitCode}），请查看上方报错`)
      return null
    }
  }
  log('⚠ 后端启动超时（40 秒），前端仍会启动，但页面拿不到数据')
  return p
}

async function ensurePreview() {
  if (await probe(PORT)) {
    log(`:${PORT} 已有服务在监听，直接复用`)
    return null
  }
  if (!fs.existsSync(path.join(FRONTEND, 'dist', 'index.html'))) {
    throw new Error('frontend/dist 不存在，请先不带 --serve-only 运行一次（会先打包）')
  }
  log('启动 vite preview …')
  const p = spawn(process.execPath, [VITE_BIN, 'preview', '--port', String(PORT), '--strictPort'], {
    cwd: FRONTEND,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  p.stdout.on('data', (d) => log('[preview] ' + d.toString().trim()))
  p.stderr.on('data', (d) => log('[preview:err] ' + d.toString().trim()))
  for (let i = 0; i < 60; i++) {
    await sleep(500)
    if (await probe(PORT)) {
      log(`预览服务就绪：http://127.0.0.1:${PORT}`)
      return p
    }
    if (p.exitCode !== null) throw new Error(`preview 进程退出（code=${p.exitCode}）`)
  }
  throw new Error('preview 启动超时')
}

function resolveNgrok() {
  const local = path.join(ROOT, 'tools', 'ngrok.exe')
  if (fs.existsSync(local)) return local
  const wingetPkg = path.join(process.env.LOCALAPPDATA || '', 'Microsoft', 'WinGet', 'Packages')
  if (fs.existsSync(wingetPkg)) {
    for (const dir of fs.readdirSync(wingetPkg)) {
      if (!/^Ngrok\.Ngrok_/i.test(dir)) continue
      const exe = path.join(wingetPkg, dir, 'ngrok.exe')
      if (fs.existsSync(exe) && fs.statSync(exe).size > 1024 * 1024) return exe
    }
  }
  return 'ngrok'
}

function cleanEnv() {
  const env = { ...process.env }
  for (const k of ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy', 'no_proxy', 'NO_PROXY']) {
    delete env[k]
  }
  return env
}

function startNgrok() {
  if (!fs.existsSync(NGROK_CONFIG)) {
    throw new Error(`找不到 ngrok 配置：${NGROK_CONFIG}（需要 version: "2" + authtoken）`)
  }
  const exe = resolveNgrok()
  log(`启动 ngrok：${exe}`)
  const child = spawn(exe, ['http', String(PORT), '--config', NGROK_CONFIG, '--log', 'stdout'], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: cleanEnv(),
  })

  let printed = false
  const handle = (text) => {
    const m = text.match(/https:\/\/[a-z0-9-]+\.ngrok-free\.[a-z]+/)
    if (m && !printed) {
      printed = true
      const url = m[0]
      log('='.repeat(58))
      log('  固定公网地址（重启后依然是这个）：')
      log('  ' + url)
      log('='.repeat(58))
      try {
        fs.writeFileSync(
          path.join(ROOT, 'TUNNEL-URL.txt'),
          `${url}\n生成时间：${new Date().toLocaleString('zh-CN')}\n本地端口：${PORT}（打包预览）\n方式：ngrok 固定域名\n`,
          'utf8',
        )
      } catch {}
      return
    }
    if (/ERR_NGROK_9009/.test(text)) log('✗ 代理环境变量未清干净（ERR_NGROK_9009）')
    else if (/ERR_NGROK_313/.test(text)) log('✗ 免费版不能自定义子域名，不要传 --url/--domain')
    else if (/ERR_NGROK_4018/.test(text)) log('✗ 未认证：authtoken 无效或未写入 tools/ngrok.yml')
    else if (/already (in use|online)/i.test(text)) log('✗ 该域名已有隧道在跑，先关掉旧的 ngrok')
    else if (text.trim()) log('[ngrok] ' + text.trim())
  }

  child.stdout.on('data', (d) => handle(d.toString()))
  child.stderr.on('data', (d) => handle(d.toString()))
  child.on('exit', (code) => log(`ngrok 进程退出（code=${code}）`))
  return child
}

// ---------------- main ----------------
log(`=== TransFlow-J 分享模式启动（${SERVE_ONLY ? '仅服务' : '打包 + 服务'}）===`)

try {
  if (!SERVE_ONLY) {
    await build()
  } else {
    const reason = needsBuild()
    if (reason) {
      log(`检测到${reason}，先补一次打包`)
      await build()
    } else {
      log('dist 已是最新，跳过打包')
    }
  }
  await ensureBackend()
  await ensurePreview()
  startNgrok()
} catch (e) {
  log('✗ ' + e.message)
  process.exit(1)
}

process.on('SIGINT', () => process.exit(0))
