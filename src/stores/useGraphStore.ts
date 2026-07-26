import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'

export const useGraphStore = defineStore('graph', () => {
  const nodes = ref<any[]>([])
  const links = shallowRef<any[]>([])
  const manualLocalEdges = ref<any[]>([])
  const permanentlyDeletedNodes = ref<Set<string>>(new Set())

  // Timeline (Reality Forks) State
  const snapshots = ref<any[]>([])
  const activeHash = ref<string | null>(null)

  const API_BASE = (window as any).API_BASE || import.meta.env.VITE_API_BASE_URL || ''

  function setNodes(newNodes: any[]) {
    nodes.value = newNodes
  }

  function setLinks(newLinks: any[]) {
    links.value = newLinks
  }

  function addNode(node: any) {
    nodes.value.push(node)
  }

  function addLocalEdge(edge: any) {
    manualLocalEdges.value.push(edge)
  }

  function markNodeDeleted(nodeId: string) {
    permanentlyDeletedNodes.value.add(nodeId)
    // Remove from nodes
    const index = nodes.value.findIndex((n: any) => n.id === nodeId)
    if (index !== -1) {
      nodes.value.splice(index, 1)
    }
  }

  // Timeline Methods
  async function fetchHistory() {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/snapshot/history` : '/api/lgnn/snapshot/history'
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        snapshots.value = data.history.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        if (snapshots.value.length > 0 && !activeHash.value) {
          activeHash.value = snapshots.value[snapshots.value.length - 1].hash
        }
      }
    } catch (err) {
      console.error("Failed to fetch timeline:", err)
    }
  }

  async function checkoutSnapshot(hash: string): Promise<boolean> {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/snapshot/checkout` : '/api/lgnn/snapshot/checkout'
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commit_hash: hash })
      })
      if (res.ok) {
        activeHash.value = hash
        return true
      }
    } catch (err) {
      console.error("Checkout failed:", err)
    }
    return false
  }

  async function createSnapshot(cType: string = 'user_manual', desc: string = 'Manual Snapshot') {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/snapshot/create` : '/api/lgnn/snapshot/create'
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: desc, commit_type: cType })
      })
      if (res.ok) {
        await fetchHistory()
      }
    } catch (err) {
      console.error("Fork failed:", err)
    }
  }

  return {
    nodes,
    links,
    manualLocalEdges,
    permanentlyDeletedNodes,
    snapshots,
    activeHash,
    setNodes,
    setLinks,
    addNode,
    addLocalEdge,
    markNodeDeleted,
    fetchHistory,
    checkoutSnapshot,
    createSnapshot
  }
})
