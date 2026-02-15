import { ref, onUnmounted } from 'vue'
import { useMindmapStore } from '../stores/mindmap'

export function useWebSocket() {
  const store = useMindmapStore()
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)

  function connect(mapId: string) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/${mapId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onclose = () => {
      connected.value = false
    }

    ws.value.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      handleMessage(msg)
    }
  }

  function handleMessage(msg: any) {
    switch (msg.type) {
      case 'connected':
        store.clientId = msg.client_id
        store.version = msg.version
        break
      case 'ack':
        store.version = msg.version
        // Node create ack: update with server data
        if (msg.original_type === 'node:create' && msg.data) {
          store.applyNodeCreate(msg.data)
        }
        break
      case 'node:create':
        if (msg.client_id !== store.clientId && msg.data) {
          store.applyNodeCreate(msg.data)
          store.version = msg.version
        }
        break
      case 'node:update':
        if (msg.client_id !== store.clientId && msg.data) {
          store.applyNodeUpdate(msg.data)
          store.version = msg.version
        }
        break
      case 'node:delete':
        if (msg.client_id !== store.clientId && msg.data) {
          store.applyNodeDelete(msg.data.id)
          store.version = msg.version
        }
        break
      case 'node:move':
        if (msg.client_id !== store.clientId && msg.data) {
          store.applyNodeUpdate(msg.data)
          store.version = msg.version
        }
        break
      case 'peer:disconnect':
        break
    }
  }

  function send(type: string, data: any) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type, data, version: store.version }))
    }
  }

  function createNode(parentId: string, content: string, id: string) {
    const position = store.getNextPosition(parentId)
    send('node:create', { id, parent_id: parentId, content, position })
  }

  function updateNode(nodeId: string, changes: Record<string, any>) {
    send('node:update', { id: nodeId, changes })
  }

  function deleteNode(nodeId: string) {
    send('node:delete', { id: nodeId })
  }

  function moveNode(nodeId: string, newParentId: string, position: number) {
    send('node:move', { id: nodeId, parent_id: newParentId, position })
  }

  function disconnect() {
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    connect,
    disconnect,
    createNode,
    updateNode,
    deleteNode,
    moveNode,
  }
}
