<template>
  <div class="editor">
    <Toolbar @back="goBack" />
    <div class="editor-body">
      <MindMapCanvas @showHistory="onShowHistory" />
      <HistoryPanel
        :visible="historyPanel.visible"
        :mapId="store.mapId || ''"
        :nodeId="historyPanel.nodeId"
        @close="historyPanel.visible = false"
        @rollback="onHistoryRollback"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { provide, ref, toRef, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMindmapStore } from '../stores/mindmap'
import { useWebSocket } from '../composables/useWebSocket'
import { useUndo } from '../composables/useUndo'
import type { UndoEntry } from '../composables/useUndo'
import Toolbar from '../components/Toolbar.vue'
import MindMapCanvas from '../components/MindMapCanvas.vue'
import HistoryPanel from '../components/HistoryPanel.vue'
import { apiJson } from '../services/api'

const route = useRoute()
const router = useRouter()
const store = useMindmapStore()
const ws = useWebSocket()
const undo = useUndo()

// History panel state
const historyPanel = ref<{ visible: boolean; nodeId: string | null }>({ visible: false, nodeId: null })

function onShowHistory(nodeId: string | null) {
  historyPanel.value = { visible: true, nodeId }
}

async function onHistoryRollback() {
  // Reload the map to get fresh data after rollback
  if (store.mapId) {
    try {
      const data = await apiJson(`/api/maps/${store.mapId}`)
      store.loadMap(data)
    } catch { /* ignore */ }
  }
}

provide('syncActions', {
  createNode: ws.createNode,
  updateNode: ws.updateNode,
  deleteNode: ws.deleteNode,
  lockNode: ws.lockNode,
  unlockNode: ws.unlockNode,
})
provide('syncing', toRef(ws, 'connected'))

function performUndo() {
  const entry = undo.popUndo()
  if (!entry) return

  if (entry.type === 'create') {
    store.applyNodeDelete(entry.nodeId)
    ws.deleteNode(entry.nodeId)
  } else if (entry.type === 'delete' && entry.deletedNodes) {
    for (const n of entry.deletedNodes) {
      store.applyNodeCreate({
        id: n.id,
        map_id: n.map_id,
        parent_id: n.parent_id,
        content: n.content,
        position: n.position,
        style: n.style,
        collapsed: n.collapsed,
      })
      ws.createNode(n.parent_id!, n.content, n.id)
    }
  } else if (entry.type === 'update' && entry.previousState) {
    const node = store.nodes.get(entry.nodeId)
    if (node) {
      Object.assign(node, entry.previousState)
      store.rebuildTree()
      ws.updateNode(entry.nodeId, entry.previousState as Record<string, any>)
    }
  }
}

provide('undoActions', {
  pushUndo: undo.pushUndo,
  canUndo: undo.canUndo,
  performUndo,
})

watch(() => store.mapId, (newId) => {
  if (newId) {
    ws.connect(newId)
  } else {
    ws.disconnect()
  }
})

onMounted(async () => {
  const mapId = route.params.id as string
  if (mapId) {
    try {
      const data = await apiJson(`/api/maps/${mapId}`)
      store.loadMap(data)
      ws.connect(mapId)
    } catch {
      router.push('/')
    }
  }
})

onUnmounted(() => {
  ws.disconnect()
  store.mapId = null
  store.selectedNodeId = null
})

function goBack() {
  ws.disconnect()
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

.editor-body {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}
</style>
