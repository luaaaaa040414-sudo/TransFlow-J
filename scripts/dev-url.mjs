#!/usr/bin/env node
/**
 * 局域网访问地址 + 服务自检。
 *
 * 用法（仓库根目录或 frontend 下）：
 *   node scripts/dev-url.mjs
 *   或 frontend 下：npm run url
 *
 * 重要：
 *  1. 本机 IP 会随网络变化（换 WiFi、重连路由器都会变）。
 *     Vite 启动时打印的 Network 地址是「启动那一刻」的，换网络后不会更新，
 *     所以换网络后要：① 重启 vite ② 重新运行本脚本确认新地址。
 *  2. 前端端口可能不是 5173 —— 5173 被占用时 Vite 会自动顺延到 5174/5175…
 *     本脚本会自动识别实际在监听的端口。
 */
import { networkInterfaces } from 'node:os'
import net from 'node:net'

const SERVICES = [
  { label: '前端页面', ports: [5173, 5174, 5175, 5176] },
  { label: '后端接口', ports: [8080] },
  { label: 'ML 服务', ports: [8000] },
]

function lanAddresses() {
  const out = []
  for (const [name, addrs] of Object.entries(networkInterfaces())) {
    for (const a of addrs || []) {
      if (a.family !== 'IPv4' || a.internal) continue
      out.push({ name, address: a.address })
    }
  }
  // 常见内网网段优先；198.18.x.x 是代理/VPN 的 TUN 虚拟网卡，排最后
  const rank = (ip) => {
    if (ip.startsWith('198.18.') || ip.startsWith('198.19.')) return 9
    if (ip.startsWith('192.168.')) return 0
    if (ip.startsWith('10.')) return 1
    if (/^172\.(1[6-9]|2\d|3[01])\./.test(ip)) return 2
    return 3
  }
  return out.sort((a, b) => rank(a.address) - rank(b.address))
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

async function resolveServices() {
  const out = []
  for (const s of SERVICES) {
    let live = null
    for (const p of s.ports) {
      if (await checkPort('127.0.0.1', p)) { live = p; break }
    }
    out.push({ label: s.label, port: live === null ? s.ports[0] : live, live: live !== null })
  }
  return out
}

const addrs = lanAddresses()

console.log('\n=== TransFlow-J 局域网访问 ===')
console.log(`检测时间：${new Date().toLocaleString('zh-CN')}\n`)

if (!addrs.length) {
  console.log('未检测到局域网 IP（没连 WiFi / 网线）。请先接入局域网再运行本脚本。\n')
  process.exit(0)
}

const primary = addrs[0]
const services = await resolveServices()

console.log(`本机当前局域网 IP：${primary.address}（网卡：${primary.name}）`)

console.log('\n【服务自检】')
for (const s of services) {
  const onLan = s.live ? await checkPort(primary.address, s.port) : false
  const state = !s.live ? '未启动' : onLan ? '正常（局域网可达）' : '仅本机可连（监听没绑 0.0.0.0？）'
  const icon = !s.live ? '×' : onLan ? '√' : '!'
  console.log(`  [${icon}] ${s.label} :${s.port}  ${state}`)
}

console.log('\n【发给同事的地址】（只发前端那条就够，页面会自动代理到后端）')
for (const s of services) {
  if (!s.live) continue
  console.log(`  ${s.label}　http://${primary.address}:${s.port}/`)
}
if (!services.some((s) => s.live)) {
  console.log('  （三个服务都没在跑，先把它们启动起来）')
}

if (addrs.length > 1) {
  console.log('\n【其他网卡】以下地址请忽略，用上面那个：')
  for (const a of addrs.slice(1)) {
    const isTun = /^198\.(18|19)\./.test(a.address)
    console.log(`  ${a.name}  ${a.address}${isTun ? '  ← 代理/VPN 虚拟网卡：浏览器会把它当外部地址走代理，自己也打不开，同事更连不上' : ''}`)
  }
}

console.log(`
【同事打不开时，按顺序排查】
  1. 地址对不对：必须用上面的局域网 IP，不能用 localhost，也不能用旧 IP
     （本机 IP 换网络就变；旧地址会一直打不开）
  2. 是否同一局域网：必须连同一个 WiFi / 同一台路由器。
     不在同一 WiFi（各自在家、用流量）时局域网 IP 完全无效。
  3. 公司或公共 WiFi 常开「AP 隔离 / 客户端隔离」，同一 WiFi 下设备之间也互相访问不了。
     验证方法：让同事在命令行执行  ping ${primary.address}
     通则说明网络可达（问题在防火墙）；不通则大概率是 AP 隔离，改用手机热点试试。
  4. 防火墙：需放行 node.exe / java.exe 的入站（本机一般已放行）
  5. 跨网络：用手机热点（两人连同一个热点），或内网穿透（frp / ngrok / Cloudflare Tunnel）。

【如果目的是「一起写代码」，局域网访问并不是正确方案】
  同事访问的只是你电脑上跑着的页面，只能看、改不了代码。
  正确做法是用 Git：代码推到 Gitee / GitHub，每人 clone 到本地各自开发，
  改完 push、别人 pull。详见 README「多人协作开发」一节。
`)
