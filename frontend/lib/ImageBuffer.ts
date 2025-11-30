/**
 * LRU Cache implementation for image buffering
 * Based on the OG project's ImageBuffer with TypeScript improvements
 */

interface CacheNode {
  key: string
  value: string | HTMLImageElement
  prev: CacheNode | null
  next: CacheNode | null
}

export class ImageBuffer {
  private readonly capacity: number
  private cache: Map<string, CacheNode>
  private head: CacheNode | null
  private tail: CacheNode | null

  constructor(capacity = 100) {
    this.capacity = capacity
    this.cache = new Map()
    this.head = null
    this.tail = null
  }

  get size(): number {
    return this.cache.size
  }

  get(key: string): string | HTMLImageElement | null {
    const node = this.cache.get(key)
    if (!node) return null

    this.moveToFront(node)
    return node.value
  }

  put(key: string, value: string | HTMLImageElement): void {
    const existingNode = this.cache.get(key)

    if (existingNode) {
      existingNode.value = value
      this.moveToFront(existingNode)
      return
    }

    const newNode = this.createNode(key, value)

    // If cache is at capacity, remove least recently used item (tail)
    if (this.cache.size >= this.capacity) {
      if (this.tail) {
        this.cache.delete(this.tail.key)
        this.tail = this.tail.prev
        if (this.tail) this.tail.next = null
        else this.head = null
      }
    }

    // Add new node to front
    this.cache.set(key, newNode)
    if (this.head) {
      newNode.next = this.head
      this.head.prev = newNode
      this.head = newNode
    } else {
      this.head = this.tail = newNode
    }
  }

  clear(): void {
    this.cache.clear()
    this.head = null
    this.tail = null
  }

  has(key: string): boolean {
    return this.cache.has(key)
  }

  private createNode(key: string, value: string | HTMLImageElement): CacheNode {
    return {
      key,
      value,
      prev: null,
      next: null
    }
  }

  private moveToFront(node: CacheNode): void {
    if (node === this.head) return

    // Remove node from its current position
    if (node.prev) node.prev.next = node.next
    if (node.next) node.next.prev = node.prev
    if (node === this.tail) this.tail = node.prev

    // Move to front
    node.next = this.head
    node.prev = null
    if (this.head) this.head.prev = node
    this.head = node
    if (!this.tail) this.tail = node
  }
}

// Global image buffer instance
export const globalImageBuffer = new ImageBuffer(100)
