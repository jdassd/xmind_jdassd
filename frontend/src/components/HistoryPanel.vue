<template>
  <div class="history-panel" v-if="visible">
    <div class="history-header">
      <span class="history-title">{{ nodeId ? 'Node History' : 'Map History' }}</span>
      <button class="history-close" @click="$emit('close')">&times;</button>
    </div>
    <div class="history-list">
      <div v-if="loading" class="history-loading">Loading...</div>
      <div v-else-if="entries.length === 0" class="history-empty">No history</div>
      <div v-else v-for="entry in entries" :key="entry.id" class="history-entry">
        <div class="history-entry-header">
          <span class="history-action" :class="entry.action">{{ actionLabel(entry.action) }}</span>
          <span class="history-user">{{ entry.username || 'Unknown' }}</span>
          <span class="history-time">{{ formatTime(entry.created_at) }}</span>
        </div>
        <div class="history-detail" v-if="entry.action === 'update'">
          <span class="history-old">{{ entry.old_content }}</span>
          <span class="history-arrow">&rarr;</span>
          <span class="history-new">{{ entry.new_content }}</span>
        </div>
        <div class="history-detail" v-else-if="entry.action === 'create'">
          Created: {{ entry.new_content }}
        </div>
        <div class="history-detail" v-else-if="entry.action === 'delete'">
          Deleted: {{ entry.old_content }}
        </div>
        <button class="history-rollback-btn" @click="rollback(entry)">Rollback</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, apiJson } from '../services/api'

const props = defineProps<{
  visible: boolean
  mapId: string
  nodeId?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'rollback'): void
}>()

const entries = ref<any[]>([])
const loading = ref(false)

watch(() => [props.visible, props.nodeId], async () => {
  if (!props.visible) return
  await fetchHistory()
}, { immediate: true })

async function fetchHistory() {
  loading.value = true
  try {
    if (props.nodeId) {
      entries.value = await apiJson(`/api/maps/${props.mapId}/nodes/${props.nodeId}/history`)
    } else {
      entries.value = await apiJson(`/api/maps/${props.mapId}/history`)
    }
  } catch {
    entries.value = []
  } finally {
    loading.value = false
  }
}

function actionLabel(action: string) {
  switch (action) {
    case 'create': return 'Create'
    case 'update': return 'Update'
    case 'delete': return 'Delete'
    default: return action
  }
}

function formatTime(dt: string) {
  if (!dt) return ''
  return new Date(dt).toLocaleString()
}

async function rollback(entry: any) {
  try {
    await api(`/api/maps/${props.mapId}/nodes/${entry.node_id}/history/${entry.id}/rollback`, {
      method: 'POST',
    })
    emit('rollback')
    await fetchHistory()
  } catch (err) {
    console.error('Rollback failed:', err)
  }
}
</script>

<style scoped>
.history-panel {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 360px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
}

.history-title {
  font-weight: 600;
  font-size: 15px;
}

.history-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  padding: 0 4px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.history-loading,
.history-empty {
  text-align: center;
  color: #999;
  padding: 24px;
  font-size: 14px;
}

.history-entry {
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.history-entry-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-action {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
  text-transform: uppercase;
}

.history-action.create {
  background: #e6f7e6;
  color: #2d8a2d;
}

.history-action.update {
  background: #e6f0ff;
  color: #2d6ab8;
}

.history-action.delete {
  background: #fde8e8;
  color: #c33;
}

.history-user {
  font-size: 12px;
  color: #666;
}

.history-time {
  font-size: 11px;
  color: #999;
  margin-left: auto;
}

.history-detail {
  font-size: 13px;
  color: #555;
  margin-bottom: 6px;
}

.history-old {
  text-decoration: line-through;
  color: #c33;
}

.history-arrow {
  margin: 0 4px;
  color: #999;
}

.history-new {
  color: #2d8a2d;
}

.history-rollback-btn {
  padding: 3px 10px;
  font-size: 12px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 3px;
  cursor: pointer;
}

.history-rollback-btn:hover {
  background: #e8e8e8;
}
</style>
