<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const menuItems = [
  { path: '/', title: '流水线总览' },
  { path: '/prep', title: '译前准备' },
  { path: '/sources', title: '信源分级' },
  { path: '/journals', title: '期刊风格库' },
  { path: '/review', title: '校对反思' }
]
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-aside">
      <div class="app-brand">
        <span class="app-brand__mark">TJ</span>
        <div>
          <div class="app-brand__name">TransFlow-J</div>
          <div class="app-brand__desc">智能翻译流水线控制台</div>
        </div>
      </div>
      <el-menu :default-active="route.path" router class="app-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          {{ item.title }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-shell { height: 100vh; }
.app-aside { border-right: 1px solid var(--el-border-color-light); }
.app-brand { display: flex; gap: 12px; align-items: center; padding: 16px; }
.app-brand__mark {
  width: 36px; height: 36px; border-radius: 8px; background: var(--el-color-primary-light-8);
  color: var(--el-color-primary); display: flex; align-items: center; justify-content: center;
  font-weight: 500; font-size: 13px;
}
.app-brand__name { font-size: 15px; font-weight: 500; }
.app-brand__desc { font-size: 12px; color: var(--el-text-color-secondary); }
.app-menu { border-right: none; }
.app-main { padding: 24px; overflow: auto; }
</style>
