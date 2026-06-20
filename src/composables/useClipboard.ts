import { Ref } from 'vue'

export function useClipboard(
  nodes: Ref<any[]>,
  links: Ref<any[]>,
  selectedNodeIds: Ref<Set<string>>,
  globalTransform: { x: number, y: number, k: number },
  API_BASE: string,
  fetchGraphData: () => Promise<void>,
  saveGraphPhysics: () => void
) {

  function copySelectedNodes() {
    const selectedNodes = nodes.value.filter(n => selectedNodeIds.value.has(n.id));
    const selectedLinks = links.value.filter(l => {
      const sId = typeof l.source === 'string' ? l.source : l.source.id;
      const tId = typeof l.target === 'string' ? l.target : l.target.id;
      return selectedNodeIds.value.has(sId) && selectedNodeIds.value.has(tId);
    });
    
    const shareData = {
      nodes: selectedNodes.map(n => ({
        id: n.id,
        label: n.label,
        content: n.content,
        node_type: n.node_type,
        meta_data: n.meta_data,
        width: n.width,
        height: n.height,
        color: n.color,
        x: n.x,
        y: n.y
      })),
      links: selectedLinks.map(l => ({
        source: typeof l.source === 'string' ? l.source : l.source.id,
        target: typeof l.target === 'string' ? l.target : l.target.id,
        weight: l.weight
      }))
    };
    
    const base64 = btoa(unescape(encodeURIComponent(JSON.stringify(shareData))));
    const shareString = `AURA://import/v1/${base64}`;
    navigator.clipboard.writeText(shareString).catch(err => console.error("Failed to copy:", err));
  }

  async function handlePaste(e: ClipboardEvent) {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
    
    const text = e.clipboardData?.getData('text');
    if (text && text.startsWith('AURA://import/v1/')) {
      e.preventDefault();
      try {
        const base64 = text.substring('AURA://import/v1/'.length);
        const shareData = JSON.parse(decodeURIComponent(escape(atob(base64))));
        
        if (!shareData.nodes || !Array.isArray(shareData.nodes)) return;
        
        const idMap = new Map<string, string>();
        const nodeUrl = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
        const edgeUrl = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
        
        const { x: tx, y: ty, k } = globalTransform;
        
        // Find bounding box center of copied nodes to offset them
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        shareData.nodes.forEach((n: any) => {
          const nx = n.x || 0;
          const ny = n.y || 0;
          if (nx < minX) minX = nx;
          if (nx > maxX) maxX = nx;
          if (ny < minY) minY = ny;
          if (ny > maxY) maxY = ny;
        });
        const groupCenterX = (minX + maxX) / 2;
        const groupCenterY = (minY + maxY) / 2;
        
        const screenCenterX = -tx / k + (window.innerWidth / 2) / k;
        const screenCenterY = -ty / k + (window.innerHeight / 2) / k;

        const shiftX = screenCenterX - groupCenterX;
        const shiftY = screenCenterY - groupCenterY;
        
        // Spawn all nodes
        for (const n of shareData.nodes) {
          const newId = `imported_${n.id}_${Date.now()}`;
          idMap.set(n.id, newId);
          
          await fetch(nodeUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id: newId,
              text_content: n.content || n.label,
              node_type: n.node_type || 'standard',
              meta_data: typeof n.meta_data === 'string' ? n.meta_data : JSON.stringify(n.meta_data || {}),
              source_tag: "imported",
              connections: []
            })
          });
        }
        
        await fetchGraphData();
        
        // Add edges
        if (shareData.links && Array.isArray(shareData.links)) {
          for (const l of shareData.links) {
            const newSource = idMap.get(l.source);
            const newTarget = idMap.get(l.target);
            if (newSource && newTarget) {
              await fetch(edgeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  source: newSource,
                  target: newTarget,
                  weight: l.weight || 1.0
                })
              });
            }
          }
        }
        
        // Add visual metadata (position + sizes) locally and sync
        nodes.value.forEach(node => {
          if (idMap.size > 0 && Array.from(idMap.values()).includes(node.id)) {
            const origId = Array.from(idMap.entries()).find(e => e[1] === node.id)?.[0];
            const origNode = shareData.nodes.find((n: any) => n.id === origId);
            if (origNode) {
              node.x = (origNode.x || 0) + shiftX + (Math.random() * 20 - 10);
              node.y = (origNode.y || 0) + shiftY + (Math.random() * 20 - 10);
              node.fx = node.x;
              node.fy = node.y;
              node.width = origNode.width;
              node.height = origNode.height;
              node.color = origNode.color;
              node.isSelected = true;
            }
          } else {
            node.isSelected = false;
          }
        });
        
        saveGraphPhysics();
      } catch (err) {
        console.error("Failed to parse AURA import", err);
      }
    }
  }

  return {
    copySelectedNodes,
    handlePaste
  }
}
