import { ref } from 'vue'
import { useMindmapStore } from '../stores/mindmap'
import { api } from '../services/api'

const POLL_INTERVAL = 1000

export function useSync() {
  const store = useMindmapStore()
  const syncing = ref(true)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let currentMapId: string | null = null

  function start(mapId: string) {
    stop()
    currentMapId = mapId
    syncing.value = true
    poll()
    pollTimer = setInterval(poll, POLL_INTERVAL)
  }

  async function poll() {
    if (!currentMapId) return
    try {
      const res = await api(`/api/maps/${currentMapId}/sync?since=${store.version}`)
      if (!res.ok) return
      const data = await res.json()

      if (data.version > store.version) {
        // Apply deletes
        for (const id of data.deleted) {
          store.applyNodeDelete(id)
        }
        // Apply creates/updates
        for (const node of data.changed) {
          if (store.nodes.has(node.id)) {
            store.applyNodeUpdate(node)
          } else {
            store.applyNodeCreate(node)
          }
        }
        store.version = data.version
      }
      syncing.value = true
    } catch {
      syncing.value = false
    }
  }

  async function createNode(parentId: string, content: string, id: string) {
    if (!currentMapId) return
    const position = store.getNextPosition(parentId)
    try {
      const res = await api(`/api/maps/${currentMapId}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, parent_id: parentId, content, position }),
      })
      if (res.ok) {
        const node = await res.json()
        store.applyNodeUpdate(node)
        store.version = node.version
      }
    } catch { /* poll will catch up */ }
  }

  async function updateNode(nodeId: string, changes: Record<string, any>) {
    if (!currentMapId) return
    try {
      const res = await api(`/api/maps/${currentMapId}/nodes/${nodeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changes),
      })
      if (res.ok) {
        const node = await res.json()
        store.applyNodeUpdate(node)
        store.version = node.version
      }
    } catch { /* poll will catch up */ }
  }

  async function deleteNode(nodeId: string) {
    if (!currentMapId) return
    try {
      const res = await api(`/api/maps/${currentMapId}/nodes/${nodeId}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        const data = await res.json()
        for (const id of data.deleted_ids) {
          store.applyNodeDelete(id)
        }
        store.version = data.version
      }
    } catch { /* poll will catch up */ }
  }

  function stop() {
    currentMapId = null
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    syncing,
    start,
    stop,
    createNode,
    updateNode,
    deleteNode,
  }
}
