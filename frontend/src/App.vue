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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
