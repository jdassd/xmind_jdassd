<template>
  <div class="editor">
    <Toolbar @back="goBack" />
    <MindMapCanvas />
  </div>
</template>

<script setup lang="ts">
import { provide, toRef, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMindmapStore } from '../stores/mindmap'
import { useSync } from '../composables/useSync'
import Toolbar from '../components/Toolbar.vue'
import MindMapCanvas from '../components/MindMapCanvas.vue'
import { apiJson } from '../services/api'

const route = useRoute()
const router = useRouter()
const store = useMindmapStore()
const sync = useSync()

provide('syncActions', {
  createNode: sync.createNode,
  updateNode: sync.updateNode,
  deleteNode: sync.deleteNode,
})
provide('syncing', toRef(sync, 'syncing'))

watch(() => store.mapId, (newId) => {
  if (newId) {
    sync.start(newId)
  } else {
    sync.stop()
  }
})

onMounted(async () => {
  const mapId = route.params.id as string
  if (mapId) {
    try {
      const data = await apiJson(`/api/maps/${mapId}`)
      store.loadMap(data)
    } catch {
      router.push('/')
    }
  }
})

onUnmounted(() => {
  sync.stop()
  store.mapId = null
  store.selectedNodeId = null
})

function goBack() {
  sync.stop()
  store.mapId = null
  store.selectedNodeId = null
  router.push('/')
}
</script>

<style scoped>
.editor {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
