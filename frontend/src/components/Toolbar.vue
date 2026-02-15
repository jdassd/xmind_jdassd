<template>
  <div class="toolbar">
    <button class="toolbar-btn" @click="$emit('back')">Back</button>
    <span class="map-name">{{ store.mapName }}</span>
    <div class="toolbar-actions">
      <button class="toolbar-btn" @click="addChild" :disabled="!store.selectedNodeId">Add Child</button>
      <button class="toolbar-btn" @click="addSibling" :disabled="!canAddSibling">Add Sibling</button>
      <button class="toolbar-btn danger" @click="deleteSelected" :disabled="!canDelete">Delete</button>
      <button class="toolbar-btn" @click="toggleCollapse" :disabled="!store.selectedNodeId">
        {{ isSelectedCollapsed ? 'Expand' : 'Collapse' }}
      </button>
    </div>
    <div class="toolbar-status">
      <span :class="['status-dot', wsConnected ? 'online' : 'offline']"></span>
      {{ wsConnected ? 'Connected' : 'Offline' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, type Ref } from 'vue'
import { useMindmapStore } from '../stores/mindmap'

const store = useMindmapStore()

const wsActions = inject<{
  createNode: (parentId: string, content: string, id: string) => void
  updateNode: (nodeId: string, changes: Record<string, any>) => void
  deleteNode: (nodeId: string) => void
}>('wsActions')!

const wsConnected = inject<Ref<boolean>>('wsConnected')!

defineEmits<{ (e: 'back'): void }>()

const canAddSibling = computed(() => {
  const node = store.selectedNode
  return node && node.parent_id !== null
})

const canDelete = computed(() => {
  const node = store.selectedNode
  return node && node.parent_id !== null
})

const isSelectedCollapsed = computed(() => {
  return store.selectedNode?.collapsed ?? false
})

function addChild() {
  if (!store.selectedNodeId) return
  const id = crypto.randomUUID()
  const content = 'New Node'
  store.applyNodeCreate({
    id,
    map_id: store.mapId!,
    parent_id: store.selectedNodeId,
    content,
    position: store.getNextPosition(store.selectedNodeId),
    style: '{}',
    collapsed: false,
  })
  wsActions.createNode(store.selectedNodeId, content, id)
  store.selectNode(id)
}

function addSibling() {
  const node = store.selectedNode
  if (!node || !node.parent_id) return
  const id = crypto.randomUUID()
  const content = 'New Node'
  store.applyNodeCreate({
    id,
    map_id: store.mapId!,
    parent_id: node.parent_id,
    content,
    position: store.getNextPosition(node.parent_id),
    style: '{}',
    collapsed: false,
  })
  wsActions.createNode(node.parent_id, content, id)
  store.selectNode(id)
}

function deleteSelected() {
  if (!store.selectedNodeId || !canDelete.value) return
  const id = store.selectedNodeId
  store.applyNodeDelete(id)
  wsActions.deleteNode(id)
}

function toggleCollapse() {
  if (!store.selectedNodeId) return
  const node = store.selectedNode
  if (!node) return
  const newCollapsed = !node.collapsed
  node.collapsed = newCollapsed
  store.rebuildTree()
  wsActions.updateNode(store.selectedNodeId, { collapsed: newCollapsed })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
  z-index: 10;
}

.map-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.toolbar-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.toolbar-btn {
  padding: 6px 14px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}

.toolbar-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.toolbar-btn.danger:hover:not(:disabled) {
  background: #fee;
  border-color: #e44;
  color: #c33;
}

.toolbar-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
  margin-left: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: #4c4;
}

.status-dot.offline {
  background: #c44;
}
</style>
