import type { MindNode } from './tree'

const NODE_H_GAP = 40   // horizontal gap between parent and children
const NODE_V_GAP = 10   // vertical gap between siblings
const NODE_MIN_WIDTH = 80
const NODE_HEIGHT = 36
const CHAR_WIDTH = 8
const NODE_PADDING = 24

export interface LayoutResult {
  nodePositions: Map<string, { x: number; y: number; width: number; height: number }>
  totalWidth: number
  totalHeight: number
}

function measureNode(node: MindNode): { width: number; height: number } {
  const textWidth = (node.content?.length || 1) * CHAR_WIDTH + NODE_PADDING
  return {
    width: Math.max(NODE_MIN_WIDTH, textWidth),
    height: NODE_HEIGHT,
  }
}

interface LayoutNode {
  node: MindNode
  width: number
  height: number
  subtreeHeight: number
  x: number
  y: number
  children: LayoutNode[]
}

function buildLayoutTree(node: MindNode): LayoutNode {
  const { width, height } = measureNode(node)
  const children: LayoutNode[] = []

  if (!node.collapsed && node.children) {
    for (const child of node.children) {
      children.push(buildLayoutTree(child))
    }
  }

  let subtreeHeight = height
  if (children.length > 0) {
    subtreeHeight = children.reduce((sum, c) => sum + c.subtreeHeight, 0) +
      (children.length - 1) * NODE_V_GAP
    subtreeHeight = Math.max(subtreeHeight, height)
  }

  return { node, width, height, subtreeHeight, x: 0, y: 0, children }
}

function assignPositions(ln: LayoutNode, x: number, y: number) {
  ln.x = x
  ln.y = y + (ln.subtreeHeight - ln.height) / 2

  if (ln.children.length > 0) {
    const childX = x + ln.width + NODE_H_GAP
    let childY = y
    for (const child of ln.children) {
      assignPositions(child, childX, childY)
      childY += child.subtreeHeight + NODE_V_GAP
    }
  }
}

function collectPositions(ln: LayoutNode, result: Map<string, { x: number; y: number; width: number; height: number }>) {
  result.set(ln.node.id, { x: ln.x, y: ln.y, width: ln.width, height: ln.height })
  for (const child of ln.children) {
    collectPositions(child, result)
  }
}

export function computeLayout(root: MindNode): LayoutResult {
  const layoutRoot = buildLayoutTree(root)
  const startX = 60
  const startY = 60
  assignPositions(layoutRoot, startX, startY)

  const positions = new Map<string, { x: number; y: number; width: number; height: number }>()
  collectPositions(layoutRoot, positions)

  let maxX = 0, maxY = 0
  for (const pos of positions.values()) {
    maxX = Math.max(maxX, pos.x + pos.width)
    maxY = Math.max(maxY, pos.y + pos.height)
  }

  return {
    nodePositions: positions,
    totalWidth: maxX + 60,
    totalHeight: maxY + 60,
  }
}
