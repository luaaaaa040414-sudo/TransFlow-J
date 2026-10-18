<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const menuOpen = ref(false)
const isHome = computed(() => route.path === '/')
const navigation = [
  { path: '/', label: '概览', active: (path: string) => path === '/' },
  { path: '/workspace', label: '翻译工作台', active: (path: string) => path === '/workspace' || path.startsWith('/project/') },
  { path: '/journals', label: '期刊规范', active: (path: string) => path === '/journals' },
  { path: '/models', label: '模型设置', active: (path: string) => path === '/models' },
]
watch(() => route.path, () => { menuOpen.value = false })
</script>

<template>
  <div class="app-container" :class="{ 'is-home': isHome }">
    <header class="site-header">
      <div class="header-inner">
        <router-link to="/" class="brand-link" aria-label="Academic QA 首页">
          <svg class="brand-symbol" width="25" height="28" viewBox="0 0 28 30" fill="none" aria-hidden="true">
            <path d="M4 22 13 4h2l9 18M8 15h12M4 26h20" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span>Academic <span class="brand-light">QA</span></span>
        </router-link>
        <nav class="desktop-nav" aria-label="主导航">
          <router-link v-for="item in navigation" :key="item.path" :to="item.path" :class="{ active: item.active(route.path) }" :aria-current="item.active(route.path) ? 'page' : undefined">{{ item.label }}</router-link>
        </nav>
        <div class="header-actions">
          <router-link :to="{ path: '/workspace', query: { create: '1' } }" class="header-cta">新建项目 <span aria-hidden="true">＋</span></router-link>
          <button class="mobile-menu-button" :aria-expanded="menuOpen" aria-controls="mobile-navigation" :aria-label="menuOpen ? '关闭导航' : '打开导航'" @click="menuOpen = !menuOpen"><span></span><span></span></button>
        </div>
      </div>
      <nav v-if="menuOpen" id="mobile-navigation" class="mobile-nav" aria-label="移动端导航">
        <router-link v-for="item in navigation" :key="item.path" :to="item.path" :class="{ active: item.active(route.path) }">{{ item.label }} <span aria-hidden="true">↗</span></router-link>
      </nav>
    </header>
    <main id="main-content" class="app-main">
      <router-view />
    </main>
    <footer class="site-footer">
      <div class="footer-top"><router-link to="/" class="footer-brand">Academic QA</router-link><span>从原文到定稿，每一步有据可循。</span></div>
      <div class="footer-bottom"><span>© 2026 Academic QA · 学术中译英工作空间</span><div><router-link to="/journals">期刊规范</router-link><router-link to="/models">模型设置</router-link><router-link to="/workspace">我的项目</router-link></div></div>
    </footer>
  </div>
</template>

<style scoped>
.app-container { min-height: 100vh; display: flex; flex-direction: column; background: var(--apple-bg); }
.site-header { position: sticky; top: 0; z-index: 100; background: rgba(250,250,252,.86); backdrop-filter: saturate(180%) blur(24px); -webkit-backdrop-filter: saturate(180%) blur(24px); border-bottom: 1px solid var(--apple-border); }
.header-inner { max-width: 1200px; min-height: 68px; margin: 0 auto; padding: 0 32px; display: flex; align-items: center; justify-content: space-between; gap: 36px; }
.brand-link { display: inline-flex; align-items: center; gap: 10px; color: var(--apple-text); text-decoration: none; font-size: 17px; font-weight: 650; letter-spacing: -.6px; white-space: nowrap; }
.brand-symbol { flex: none; }.brand-light { font-weight: 400; }
.desktop-nav { display: flex; gap: 36px; align-items: center; }
.desktop-nav a { position: relative; color: #626269; text-decoration: none; font-size: 12px; padding: 25px 0; transition: color .2s; }
.desktop-nav a:hover,.desktop-nav a.active { color: #1d1d1f; }
.desktop-nav a.active::after { position: absolute; content: ''; bottom: 13px; left: calc(50% - 2px); width: 4px; height: 4px; border-radius: 50%; background: currentColor; }
.header-actions { display: flex; align-items: center; gap: 18px; }.header-cta { display: flex; align-items: center; gap: 12px; text-decoration: none; background: var(--apple-blue); border-radius: 999px; color: white; padding: 8px 17px; font-size: 12px; transition: background .2s; }.header-cta:hover { background: var(--apple-blue-hover); }
.mobile-menu-button { display: none; background: transparent; border: 0; padding: 8px; width: 34px; cursor: pointer; }.mobile-menu-button span { display: block; height: 1.5px; background: #1d1d1f; margin: 5px 0; }
.mobile-nav { padding: 8px 24px 24px; border-top: 1px solid var(--apple-border); }.mobile-nav a { display: flex; justify-content: space-between; text-decoration: none; color: #6e6e73; padding: 14px 0; font-size: 16px; }.mobile-nav a.active { color: var(--apple-blue); }
.app-main { flex: 1; width: 100%; max-width: 1200px; margin: 0 auto; padding: 48px 32px 88px; }.is-home .app-main { max-width: none; padding: 0; }
.site-footer { padding: 0 32px; background: #f5f5f7; color: #6e6e73; font-size: 12px; }.footer-top,.footer-bottom { max-width: 1136px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 20px; }.footer-top { padding: 32px 0; border-bottom: 1px solid var(--apple-border); }.footer-brand { color: #1d1d1f; font-size: 16px; font-weight: 600; text-decoration: none; letter-spacing: -.4px; }.footer-bottom { padding: 20px 0 26px; }.footer-bottom div { display: flex; gap: 24px; }.footer-bottom a { color: #626269; text-decoration: none; }.footer-bottom a:hover { text-decoration: underline; }
@media(max-width: 900px) { .header-inner { gap: 24px; }.desktop-nav { gap: 22px; } }
@media(max-width: 700px) { .header-inner { padding: 0 20px; min-height: 60px; gap: 12px; }.desktop-nav { display: none; }.mobile-menu-button { display: block; }.brand-link { font-size: 16px; }.header-cta { padding: 7px 12px; }.header-actions { gap: 10px; }.app-main { padding: 28px 20px 56px; }.site-footer { padding: 0 20px; }.footer-top,.footer-bottom { align-items: flex-start; flex-direction: column; gap: 12px; }.footer-bottom div { flex-wrap: wrap; } }
</style>
