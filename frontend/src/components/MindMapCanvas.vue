<template>
  <div
    class="canvas-container"
    ref="containerRef"
    @wheel="onWheel"
    @mousedown="onCanvasMouseDown"
    @mousemove="onCanvasMouseMove"
    @mouseup="onCanvasMouseUp"
    @dblclick="onDoubleClick"
  >
    <canvas ref="canvasRef"></canvas>
    <!-- Inline text editing -->
    <input
      v-if="editing"
      ref="editInputRef"
      class="edit-input"
      :style="editInputStyle"
      v-model="editText"
      @blur="finishEdit"
      @keyup.enter="finishEdit"
      @keyup.escape="cancelEdit"
    />
    <Minimap :viewport="viewport" :layout="store.layout" @navigate="onMinimapNavigate" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick, provide, toRef } from 'vue'
import { useMindmapStore } from '../stores/mindmap'
import { useWebSocket } from '../composables/useWebSocket'
import Minimap from './Minimap.vue'

const store = useMindmapStore()
const ws = useWebSocket()

// Provide ws actions and connection status to child components
provide('wsActions', {
  createNode: ws.createNode,
  updateNode: ws.updateNode,
  deleteNode: ws.deleteNode,
  moveNode: ws.moveNode,
})
provide('wsConnected', toRef(ws, 'connected'))

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()

// Viewport state
const viewport = ref({ x: 0, y: 0, scale: 1 })
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const panViewportStart = ref({ x: 0, y: 0 })

// Edit state
const editing = ref(false)
const editNodeId = ref<string | null>(null)
const editText = ref('')
const editInputRef = ref<HTMLInputElement>()

const editInputStyle = computed(() => {
  if (!editing.value || !editNodeId.value || !store.layout) return {}
  const pos = store.layout.nodePositions.get(editNodeId.value)
  if (!pos) return {}
  const v = viewport.value
  return {
    left: `${pos.x * v.scale + v.x}px`,
    top: `${pos.y * v.scale + v.y}px`,
    width: `${pos.width * v.scale}px`,
    height: `${pos.height * v.scale}px`,
    fontSize: `${14 * v.scale}px`,
  }
})

// Colors
const COLORS = {
  bg: '#fafafa',
  nodeFill: '#ffffff',
  nodeStroke: '#d0d0d0',
  nodeText: '#333333',
  selectedStroke: '#4a9eff',
  rootFill: '#4a9eff',
  rootText: '#ffffff',
  line: '#c0c0c0',
  collapsedDot: '#ff9944',
}

function draw() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const dpr = window.devicePixelRatio || 1
  const w = container.clientWidth
  const h = container.clientHeight
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = `${w}px`
  canvas.style.height = `${h}px`

  const ctx = canvas.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  // Clear
  ctx.fillStyle = COLORS.bg
  ctx.fillRect(0, 0, w, h)

  if (!store.root || !store.layout) return

  const v = viewport.value
  ctx.save()
  ctx.translate(v.x, v.y)
  ctx.scale(v.scale, v.scale)

  // Viewport culling bounds (in world coordinates)
  const vx0 = -v.x / v.scale
  const vy0 = -v.y / v.scale
  const vx1 = (w - v.x) / v.scale
  const vy1 = (h - v.y) / v.scale

  const positions = store.layout.nodePositions

  // Draw connections
  ctx.strokeStyle = COLORS.line
  ctx.lineWidth = 1.5
  for (const node of store.nodes.values()) {
    if (node.parent_id === null) continue
    const childPos = positions.get(node.id)
    const parentPos = positions.get(node.parent_id)
    if (!childPos || !parentPos) continue

    // Cull if both nodes outside viewport
    const minX = Math.min(parentPos.x, childPos.x)
    const maxX = Math.max(parentPos.x + parentPos.width, childPos.x + childPos.width)
    const minY = Math.min(parentPos.y, childPos.y)
    const maxY = Math.max(parentPos.y + parentPos.height, childPos.y + childPos.height)
    if (maxX < vx0 || minX > vx1 || maxY < vy0 || minY > vy1) continue

    const x1 = parentPos.x + parentPos.width
    const y1 = parentPos.y + parentPos.height / 2
    const x2 = childPos.x
    const y2 = childPos.y + childPos.height / 2
    const cx = (x1 + x2) / 2

    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.bezierCurveTo(cx, y1, cx, y2, x2, y2)
    ctx.stroke()
  }

  // Draw nodes
  for (const [nodeId, pos] of positions) {
    // Viewport culling
    if (pos.x + pos.width < vx0 || pos.x > vx1 || pos.y + pos.height < vy0 || pos.y > vy1) continue

    const node = store.nodes.get(nodeId)
    if (!node) continue
    const isRoot = node.parent_id === null
    const isSelected = nodeId === store.selectedNodeId

    // Node background
    ctx.fillStyle = isRoot ? COLORS.rootFill : COLORS.nodeFill
    ctx.strokeStyle = isSelected ? COLORS.selectedStroke : COLORS.nodeStroke
    ctx.lineWidth = isSelected ? 2.5 : 1
    const r = 6
    ctx.beginPath()
    ctx.roundRect(pos.x, pos.y, pos.width, pos.height, r)
    ctx.fill()
    ctx.stroke()

    // Text
    ctx.fillStyle = isRoot ? COLORS.rootText : COLORS.nodeText
    ctx.font = '14px -apple-system, BlinkMacSystemFont, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const text = node.content || ''
    const maxTextW = pos.width - 16
    let displayText = text
    if (ctx.measureText(text).width > maxTextW) {
      while (ctx.measureText(displayText + '...').width > maxTextW && displayText.length > 0) {
        displayText = displayText.slice(0, -1)
      }
      displayText += '...'
    }
    ctx.fillText(displayText, pos.x + pos.width / 2, pos.y + pos.height / 2)

    // Collapsed indicator
    if (node.collapsed) {
      ctx.fillStyle = COLORS.collapsedDot
      ctx.beginPath()
      ctx.arc(pos.x + pos.width + 8, pos.y + pos.height / 2, 4, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  ctx.restore()
}

function screenToWorld(sx: number, sy: number) {
  const v = viewport.value
  return {
    x: (sx - v.x) / v.scale,
    y: (sy - v.y) / v.scale,
  }
}

function hitTest(sx: number, sy: number): string | null {
  if (!store.layout) return null
  const world = screenToWorld(sx, sy)
  for (const [nodeId, pos] of store.layout.nodePositions) {
    if (world.x >= pos.x && world.x <= pos.x + pos.width &&
        world.y >= pos.y && world.y <= pos.y + pos.height) {
      return nodeId
    }
  }
  return null
}

function onCanvasMouseDown(e: MouseEvent) {
  if (editing.value) return
  const rect = containerRef.value!.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const nodeId = hitTest(sx, sy)

  if (nodeId) {
    store.selectNode(nodeId)
    draw()
  } else {
    store.selectNode(null)
    isPanning.value = true
    panStart.value = { x: e.clientX, y: e.clientY }
    panViewportStart.value = { x: viewport.value.x, y: viewport.value.y }
    draw()
  }
}

function onCanvasMouseMove(e: MouseEvent) {
  if (!isPanning.value) return
  viewport.value.x = panViewportStart.value.x + (e.clientX - panStart.value.x)
  viewport.value.y = panViewportStart.value.y + (e.clientY - panStart.value.y)
  draw()
}

function onCanvasMouseUp() {
  isPanning.value = false
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  const rect = containerRef.value!.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.min(3, Math.max(0.1, viewport.value.scale * zoomFactor))

  // Zoom toward cursor
  viewport.value.x = mx - (mx - viewport.value.x) * (newScale / viewport.value.scale)
  viewport.value.y = my - (my - viewport.value.y) * (newScale / viewport.value.scale)
  viewport.value.scale = newScale
  draw()
}

function onDoubleClick(e: MouseEvent) {
  const rect = containerRef.value!.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const nodeId = hitTest(sx, sy)
  if (nodeId) {
    startEdit(nodeId)
  }
}

function startEdit(nodeId: string) {
  const node = store.nodes.get(nodeId)
  if (!node) return
  editNodeId.value = nodeId
  editText.value = node.content
  editing.value = true
  store.selectNode(nodeId)
  nextTick(() => {
    editInputRef.value?.focus()
    editInputRef.value?.select()
  })
}

function finishEdit() {
  if (!editing.value || !editNodeId.value) return
  const node = store.nodes.get(editNodeId.value)
  if (node && editText.value !== node.content) {
    node.content = editText.value
    store.rebuildTree()
    ws.updateNode(editNodeId.value, { content: editText.value })
  }
  editing.value = false
  editNodeId.value = null
  draw()
}

function cancelEdit() {
  editing.value = false
  editNodeId.value = null
  draw()
}

function onKeydown(e: KeyboardEvent) {
  if (editing.value) return
  if (!store.selectedNodeId) return

  if (e.key === 'Tab') {
    e.preventDefault()
    // Add child
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
    ws.createNode(store.selectedNodeId, content, id)
    store.selectNode(id)
    draw()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const node = store.selectedNode
    if (node?.parent_id) {
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
      ws.createNode(node.parent_id, content, id)
      store.selectNode(id)
      draw()
    }
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    const node = store.selectedNode
    if (node && node.parent_id !== null) {
      store.applyNodeDelete(node.id)
      ws.deleteNode(node.id)
      draw()
    }
  } else if (e.key === 'F2' || e.key === ' ') {
    e.preventDefault()
    startEdit(store.selectedNodeId)
  }
}

function onMinimapNavigate(pos: { x: number; y: number }) {
  const container = containerRef.value
  if (!container) return
  viewport.value.x = -pos.x * viewport.value.scale + container.clientWidth / 2
  viewport.value.y = -pos.y * viewport.value.scale + container.clientHeight / 2
  draw()
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (store.mapId) {
    ws.connect(store.mapId)
  }

  draw()

  resizeObserver = new ResizeObserver(() => draw())
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }

  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('keydown', onKeydown)
})

// Redraw when layout changes
watch(() => store.layout, () => draw(), { deep: false })

// Connect when map changes
watch(() => store.mapId, (newId) => {
  if (newId) {
    ws.connect(newId)
  } else {
    ws.disconnect()
  }
})
</script>

<style scoped>
.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: grab;
}

.canvas-container:active {
  cursor: grabbing;
}

canvas {
  display: block;
}

.edit-input {
  position: absolute;
  border: 2px solid #4a9eff;
  border-radius: 4px;
  padding: 2px 8px;
  outline: none;
  text-align: center;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  background: #fff;
  z-index: 20;
}
</style>
