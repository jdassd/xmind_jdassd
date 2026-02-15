<template>
  <div class="minimap" ref="minimapRef" @mousedown="onMinimapClick">
    <canvas ref="minimapCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { LayoutResult } from '../utils/layout'

const props = defineProps<{
  viewport: { x: number; y: number; scale: number }
  layout: LayoutResult | null
}>()

const emit = defineEmits<{
  (e: 'navigate', pos: { x: number; y: number }): void
}>()

const minimapRef = ref<HTMLDivElement>()
const minimapCanvas = ref<HTMLCanvasElement>()

const MINIMAP_W = 180
const MINIMAP_H = 120

function draw() {
  const canvas = minimapCanvas.value
  if (!canvas || !props.layout) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = MINIMAP_W * dpr
  canvas.height = MINIMAP_H * dpr
  canvas.style.width = `${MINIMAP_W}px`
  canvas.style.height = `${MINIMAP_H}px`

  const ctx = canvas.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  ctx.fillStyle = 'rgba(255,255,255,0.9)'
  ctx.fillRect(0, 0, MINIMAP_W, MINIMAP_H)

  const tw = props.layout.totalWidth || 1
  const th = props.layout.totalHeight || 1
  const scaleX = (MINIMAP_W - 10) / tw
  const scaleY = (MINIMAP_H - 10) / th
  const s = Math.min(scaleX, scaleY)

  ctx.save()
  ctx.translate(5, 5)
  ctx.scale(s, s)

  // Draw nodes as small dots
  ctx.fillStyle = '#4a9eff'
  for (const pos of props.layout.nodePositions.values()) {
    ctx.fillRect(pos.x, pos.y, Math.max(pos.width, 3 / s), Math.max(pos.height, 2 / s))
  }

  ctx.restore()

  // Draw viewport rect
  const v = props.viewport
  const parentEl = minimapRef.value?.parentElement
  if (parentEl) {
    const pw = parentEl.clientWidth
    const ph = parentEl.clientHeight
    const vx = (-v.x / v.scale) * s + 5
    const vy = (-v.y / v.scale) * s + 5
    const vw = (pw / v.scale) * s
    const vh = (ph / v.scale) * s
    ctx.strokeStyle = '#e44'
    ctx.lineWidth = 1.5
    ctx.strokeRect(vx, vy, vw, vh)
  }
}

function onMinimapClick(e: MouseEvent) {
  const rect = minimapRef.value!.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  if (!props.layout) return

  const tw = props.layout.totalWidth || 1
  const th = props.layout.totalHeight || 1
  const scaleX = (MINIMAP_W - 10) / tw
  const scaleY = (MINIMAP_H - 10) / th
  const s = Math.min(scaleX, scaleY)

  const worldX = (mx - 5) / s
  const worldY = (my - 5) / s

  emit('navigate', { x: worldX, y: worldY })
}

watch(() => [props.viewport, props.layout], () => draw(), { deep: true })
onMounted(() => draw())
</script>

<style scoped>
.minimap {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 180px;
  height: 120px;
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  cursor: crosshair;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
