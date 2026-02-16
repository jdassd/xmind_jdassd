<template>
  <header class="app-header">
    <router-link to="/" class="logo">MindMap</router-link>
    <nav class="nav-links">
      <router-link to="/">Maps</router-link>
      <router-link to="/teams">Teams</router-link>
    </nav>
    <div class="user-menu">
      <span class="user-name">{{ auth.user?.display_name || auth.user?.username }}</span>
      <button class="btn-logout" @click="handleLogout">Logout</button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 20px;
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  color: #4a9eff;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 16px;
}

.nav-links a {
  font-size: 14px;
  color: #555;
  text-decoration: none;
  padding: 4px 0;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #4a9eff;
}

.user-menu {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 13px;
  color: #666;
}

.btn-logout {
  padding: 4px 12px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.btn-logout:hover {
  border-color: #e44;
  color: #e44;
}
</style>
