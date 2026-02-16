<template>
  <div class="app">
    <AppHeader v-if="auth.isAuthenticated && !isEditorRoute" />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/AppHeader.vue'

const auth = useAuthStore()
const route = useRoute()

const isEditorRoute = computed(() => route.name === 'map-editor')
</script>

<style>
:root {
  /* Surface palette */
  --bg-base: #0c0c10;
  --bg-surface: #141419;
  --bg-elevated: #1c1c24;
  --bg-hover: #24242e;
  --bg-active: #2c2c38;

  /* Border palette */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.16);

  /* Text palette */
  --text-primary: #e8e8ed;
  --text-secondary: #9494a3;
  --text-tertiary: #5f5f72;
  --text-inverse: #0c0c10;

  /* Accent palette */
  --accent: #38bdf8;
  --accent-hover: #56ccf9;
  --accent-glow: rgba(56, 189, 248, 0.15);
  --accent-glow-strong: rgba(56, 189, 248, 0.25);

  /* Secondary accent */
  --accent-green: #34d399;
  --accent-green-glow: rgba(52, 211, 153, 0.15);

  /* Semantic colors */
  --color-error: #f87171;
  --color-error-bg: rgba(248, 113, 113, 0.1);
  --color-warning: #fbbf24;
  --color-warning-bg: rgba(251, 191, 36, 0.1);
  --color-success: #34d399;
  --color-success-bg: rgba(52, 211, 153, 0.1);
  --color-info: #38bdf8;
  --color-info-bg: rgba(56, 189, 248, 0.1);

  /* Typography */
  --font-display: 'Sora', sans-serif;
  --font-body: 'DM Sans', sans-serif;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.5), 0 2px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.6), 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 20px rgba(56, 189, 248, 0.15), 0 0 60px rgba(56, 189, 248, 0.05);

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  /* Transitions */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 0.15s;
  --duration-normal: 0.25s;
  --duration-slow: 0.4s;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: var(--font-body);
  background: var(--bg-base);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* Selection */
::selection {
  background: var(--accent-glow-strong);
  color: var(--text-primary);
}

.app {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Global focus styles */
*:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
</style>
