<template>
  <el-container class="app-container">
    <!-- Apple-style Frosted Glass Top Navigation -->
    <header class="apple-header">
      <div class="header-inner">
        <!-- Brand Logo Group -->
        <router-link to="/" class="brand-link">
          <div class="brand-symbol">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#0071e3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="#0071e3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="#0071e3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="brand-texts">
            <span class="brand-title">Academic QA</span>
            <span class="brand-subtitle">学术中译英质量保障平台</span>
          </div>
          <span class="brand-badge">A0-D5 闭环</span>
        </router-link>

        <!-- Center Nav Items -->
        <nav class="nav-links">
          <router-link
            to="/"
            class="nav-item"
            :class="{ active: $route.path === '/' }"
          >
            <el-icon><InfoFilled /></el-icon>
            <span>项目介绍</span>
          </router-link>
          <router-link
            to="/workspace"
            class="nav-item"
            :class="{ active: $route.path === '/workspace' || $route.path.startsWith('/project/') }"
          >
            <el-icon><House /></el-icon>
            <span>翻译工作台</span>
          </router-link>
          <router-link
            to="/journals"
            class="nav-item"
            :class="{ active: $route.path === '/journals' }"
          >
            <el-icon><Reading /></el-icon>
            <span>顶刊规范库 (11本)</span>
          </router-link>
          <router-link
            to="/models"
            class="nav-item"
            :class="{ active: $route.path === '/models' }"
          >
            <el-icon><Setting /></el-icon>
            <span>模型配置</span>
          </router-link>
        </nav>

        <!-- Right Status & Actions -->
        <div class="header-right">
          <div class="engine-status">
            <span class="status-dot"></span>
            <span class="status-text">DeepSeek & MQM 引擎已就绪</span>
          </div>
          <el-button
            type="primary"
            size="small"
            class="apple-cta-btn"
            @click="$router.push('/workspace')"
          >
            进入工作台 ↗
          </el-button>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="app-main">
      <router-view />
    </main>

    <!-- Apple-style Minimalist Footer -->
    <footer class="apple-footer">
      <div class="footer-inner">
        <div class="footer-copy">
          © 2026 学术中译英质量保障平台 · Academic Translation QA Framework (A0-D5)
        </div>
        <div class="footer-links">
          <span>四件套译前约束 (Brief / 术语 / Style / Numbers)</span>
          <span class="dot-sep">·</span>
          <span>跨厂商多模型 MQM 独立互审</span>
          <span class="dot-sep">·</span>
          <span>确定性数字零容忍门禁</span>
        </div>
      </div>
    </footer>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { House, Reading, Setting, Plus, InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()

const triggerCreate = () => {
  if (window.location.pathname !== '/') {
    router.push({ path: '/', query: { create: '1' } })
  } else {
    window.dispatchEvent(new CustomEvent('open-create-project-dialog'))
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--apple-bg);
}

/* Apple Frosted Glass Header */
.apple-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 56px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.header-inner {
  max-width: 1360px;
  height: 100%;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Brand Group */
.brand-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--apple-text);
  transition: opacity 0.2s ease;
}

.brand-link:hover {
  opacity: 0.85;
}

.brand-symbol {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(0, 113, 227, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-texts {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1d1d1f;
}

.brand-subtitle {
  font-size: 11px;
  color: #86868b;
  font-weight: 400;
}

.brand-badge {
  font-size: 10px;
  font-weight: 700;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 2px 7px;
  border-radius: 980px;
  letter-spacing: 0.02em;
}

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.04);
  padding: 4px;
  border-radius: 980px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 980px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  color: #6e6e73;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.nav-item:hover {
  color: #1d1d1f;
  background: rgba(255, 255, 255, 0.5);
}

.nav-item.active {
  color: #1d1d1f;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

/* Header Right */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.engine-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #86868b;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #34c759;
  box-shadow: 0 0 8px rgba(52, 199, 89, 0.6);
  animation: pulse-dot 2s infinite ease-in-out;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

.status-text {
  font-weight: 500;
}

.apple-cta-btn {
  border-radius: 980px !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
}

/* Main */
.app-main {
  flex: 1;
  max-width: 1360px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

/* Footer */
.apple-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #ffffff;
  padding: 24px 0;
  font-size: 12px;
  color: #86868b;
}

.footer-inner {
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot-sep {
  opacity: 0.5;
}

@media (max-width: 900px) {
  .brand-subtitle, .engine-status {
    display: none;
  }
  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
