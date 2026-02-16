<template>
  <div class="toolbar">
    <button class="toolbar-btn back-btn" @click="$emit('back')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
    </button>
    <div class="toolbar-divider"></div>
    <span class="map-name">{{ store.mapName }}</span>
    <div class="toolbar-actions">
      <button class="toolbar-btn" @click="addChild" :disabled="!store.selectedNodeId" title="Add Child (Tab)">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Child
      </button>
      <button class="toolbar-btn" @click="addSibling" :disabled="!canAddSibling" title="Add Sibling (Enter)">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Sibling
      </button>
      <button class="toolbar-btn danger" @click="deleteSelected" :disabled="!canDelete" title="Delete (Del)">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>
      <div class="toolbar-divider"></div>
      <button class="toolbar-btn" @click="undoActions.performUndo()" :disabled="!undoActions.canUndo.value" title="Undo (Ctrl+Z)">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
      </button>
      <button class="toolbar-btn" @click="toggleCollapse" :disabled="!store.selectedNodeId" :title="isSelectedCollapsed ? 'Expand' : 'Collapse'">
        <svg v-if="isSelectedCollapsed" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
        <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
      </button>
    </div>
    <div class="toolbar-status">
      <span :class="['status-dot', syncing ? 'online' : 'offline']"></span>
      {{ syncing ? 'Synced' : 'Offline' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, type Ref, type ComputedRef } from 'vue'
import { useMindmapStore } from '../stores/mindmap'
import type { MindNode } from '../utils/tree'
import type { UndoEntry } from '../composables/useUndo'

const store = useMindmapStore()

const actions = inject<{
  createNode: (parentId: string, content: string, id: string) => void
  updateNode: (nodeId: string, changes: Record<string, any>) => void
  deleteNode: (nodeId: string) => void
  lockNode: (nodeId: string) => Promise<boolean>
  unlockNode: (nodeId: string) => Promise<void>
}>('syncActions')!

const syncing = inject<Ref<boolean>>('syncing')!

const undoActions = inject<{
  pushUndo: (entry: UndoEntry) => void
  canUndo: ComputedRef<boolean>
  performUndo: () => void
}>('undoActions')!

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
  actions.createNode(store.selectedNodeId, content, id)
  undoActions.pushUndo({ type: 'create', nodeId: id })
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
  actions.createNode(node.parent_id, content, id)
  undoActions.pushUndo({ type: 'create', nodeId: id })
  store.selectNode(id)
}

function collectSubtreeSnapshot(nodeId: string): MindNode[] {
  const result: MindNode[] = []
  const node = store.nodes.get(nodeId)
  if (!node) return result
  result.push({ ...node })
  for (const n of store.nodes.values()) {
    if (n.parent_id === nodeId) {
      result.push(...collectSubtreeSnapshot(n.id))
    }
  }
  return result
}

function deleteSelected() {
  if (!store.selectedNodeId || !canDelete.value) return
  const id = store.selectedNodeId
  const snapshot = collectSubtreeSnapshot(id)
  undoActions.pushUndo({ type: 'delete', nodeId: id, deletedNodes: snapshot })
  store.applyNodeDelete(id)
  actions.deleteNode(id)
}

function toggleCollapse() {
  if (!store.selectedNodeId) return
  const node = store.selectedNode
  if (!node) return
  const newCollapsed = !node.collapsed
  node.collapsed = newCollapsed
  store.rebuildTree()
  actions.updateNode(store.selectedNodeId, { collapsed: newCollapsed })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 10;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: var(--border-subtle);
  margin: 0 4px;
}

.map-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-body);
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-out);
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.toolbar-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.back-btn {
  padding: 6px 8px;
}

.toolbar-btn.danger:hover:not(:disabled) {
  background: var(--color-error-bg);
  border-color: rgba(248, 113, 113, 0.3);
  color: var(--color-error);
}

.toolbar-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-tertiary);
  margin-left: 12px;
  padding: 4px 10px;
  background: var(--bg-elevated);
  border-radius: 20px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--accent-green);
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.5);
}

.status-dot.offline {
  background: var(--color-error);
  box-shadow: 0 0 6px rgba(248, 113, 113, 0.5);
}
</style>
