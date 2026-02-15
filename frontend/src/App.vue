<template>
  <div class="app">
    <div v-if="!store.mapId" class="landing">
      <h1>MindMap</h1>
      <div class="map-list">
        <div v-for="m in maps" :key="m.id" class="map-item" @click="openMap(m.id)">
          <span>{{ m.name }}</span>
          <button class="btn-delete" @click.stop="removeMap(m.id)">x</button>
        </div>
      </div>
      <div class="create-form">
        <input v-model="newMapName" placeholder="New map name..." @keyup.enter="createNewMap" />
        <button @click="createNewMap">Create</button>
      </div>
    </div>
    <div v-else class="editor">
      <Toolbar @back="goBack" />
      <MindMapCanvas />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide, toRef, watch, onMounted, onUnmounted } from 'vue'
import { useMindmapStore } from './stores/mindmap'
import { useWebSocket } from './composables/useWebSocket'
import Toolbar from './components/Toolbar.vue'
import MindMapCanvas from './components/MindMapCanvas.vue'

const store = useMindmapStore()
const ws = useWebSocket()
const maps = ref<any[]>([])
const newMapName = ref('')

// Provide WebSocket actions and connection status to all children
provide('wsActions', {
  createNode: ws.createNode,
  updateNode: ws.updateNode,
  deleteNode: ws.deleteNode,
  moveNode: ws.moveNode,
})
provide('wsConnected', toRef(ws, 'connected'))

// Manage WebSocket lifecycle based on current map
watch(() => store.mapId, (newId) => {
  if (newId) {
    ws.connect(newId)
  } else {
    ws.disconnect()
  }
})

onUnmounted(() => {
  ws.disconnect()
})

async function fetchMaps() {
  const res = await fetch('/api/maps')
  maps.value = await res.json()
}

async function createNewMap() {
  const name = newMapName.value.trim()
  if (!name) return
  const res = await fetch('/api/maps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  newMapName.value = ''
  await fetchMaps()
  openMap(data.id)
}

async function openMap(id: string) {
  const res = await fetch(`/api/maps/${id}`)
  const data = await res.json()
  store.loadMap(data)
}

async function removeMap(id: string) {
  await fetch(`/api/maps/${id}`, { method: 'DELETE' })
  await fetchMaps()
}

function goBack() {
  ws.disconnect()
  store.mapId = null
  store.selectedNodeId = null
  fetchMaps()
}

onMounted(fetchMaps)
</script>

<style>
.app {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 80px;
  gap: 20px;
}

.landing h1 {
  font-size: 32px;
  color: #333;
}

.map-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 360px;
}

.map-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.map-item:hover {
  background: #e8e8e8;
}

.btn-delete {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 2px 8px;
}

.btn-delete:hover {
  color: #e44;
}

.create-form {
  display: flex;
  gap: 8px;
  width: 360px;
}

.create-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.create-form input:focus {
  border-color: #4a9eff;
}

.create-form button {
  padding: 10px 20px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.create-form button:hover {
  background: #3a8eef;
}

.editor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
