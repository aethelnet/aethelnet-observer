import { useGraphStore } from '../stores/useGraphStore'

const API_BASE = (window as any).API_BASE || import.meta.env.VITE_API_BASE_URL || ''

export function useLgnnData() {
  const store = useGraphStore()

  async function updateNode(node: any, options: any = {}) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: node.id,
          text_content: node.content || node.label || '',
          meta_data: node.meta_data || "{}",
          source_tag: node.source_tag || "manual",
          connections: [],
          parent_id: node.parent_id || 'root'
        })
      })
      // Trigger update is handled via WebSocket usually, but we could trigger manual fetch
    } catch(e) {
      console.error("Failed to update node", e)
    }
  }

  async function createLink(sourceId: string, targetId: string) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: sourceId,
          target: targetId,
          weight: 1.0,
          is_manual: true
        })
      })
    } catch(e) {
      console.error('Failed to create edge', e)
    }
  }

  async function deleteLink(link: any) {
    // If it's a manual local edge, remove it
    const storeEdges = store.manualLocalEdges.filter((e: any) => e !== link)
    store.manualLocalEdges = storeEdges
    
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source
    const targetId = typeof link.target === 'object' ? link.target.id : link.target
    
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
      await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: sourceId, target: targetId })
      })
    } catch (err) {
      console.error("Failed to delete edge:", err)
    }
  }

  async function spawnOmniDecoder(targetNode: any, parentId: string) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
      const decoderId = 'omni_decoder_' + Date.now();
      
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: decoderId,
          text_content: "",
          node_type: "standard",
          source_tag: "omni_decoder",
          meta_data: JSON.stringify({
            target_id: targetNode.id,
            mode: "TEXT"
          }),
          is_grounded: true,
          confidence: 1.0,
          parent_id: parentId
        })
      });
      
      const edgeUrl = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
      await fetch(edgeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: targetNode.id,
          target: decoderId,
          weight: 1.0,
          is_manual: true
        })
      });
    } catch (err) {
      console.error('Failed to spawn omni decoder:', err)
    }
  }

  async function deleteSelectedNodes(selectedIds: string[]) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
      await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: selectedIds })
      });
      selectedIds.forEach(id => store.markNodeDeleted(id));
    } catch(e) {
      console.error("Failed to delete nodes", e);
    }
  }

  async function mergeNodes(selectedIds: string[]) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/macro/compress` : '/api/lgnn/macro/compress';
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_ids: selectedIds })
      })
      const data = await res.json()
      return data
    } catch (err) {
      console.error('Compression failed:', err)
      return { status: 'error' }
    }
  }

  return {
    updateNode,
    createLink,
    deleteLink,
    spawnOmniDecoder,
    deleteSelectedNodes,
    mergeNodes
  }
}
