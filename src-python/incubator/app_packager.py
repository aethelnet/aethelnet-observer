import json
import logging
import uuid
from lgnn.database import execute_query, save_node, save_edge, load_graph_state
import torch

logger = logging.getLogger("AppPackager")

def export_app(root_id: str, app_name: str, author: str) -> str:
    """
    Traverses the graph starting from root_id and bundles all connected nodes
    and their edges into a decentralized AuraticAppPackage (JSON).
    """
    logger.info(f"Exporting App Bundle starting at {root_id}...")
    
    # Simple BFS to find all connected nodes in this app's subgraph
    queue = [root_id]
    visited_nodes = set()
    edges_to_export = []
    
    # We load the entire graph for traversal efficiency
    nodes, edges, _ = load_graph_state(dim=128)
    
    if root_id not in nodes:
        raise ValueError(f"Root node {root_id} not found in graph.")
        
    while queue:
        current = queue.pop(0)
        if current in visited_nodes:
            continue
        visited_nodes.add(current)
        
        # Find all outgoing and incoming edges for 'current'
        for edge in edges:
            src, tgt, weight, label = edge[0], edge[1], edge[2], edge[3] if len(edge) > 3 else "connects_to"
            if src == current and tgt not in visited_nodes:
                queue.append(tgt)
                edges_to_export.append({"source": src, "target": tgt, "weight": weight, "label": label})
            elif tgt == current and src not in visited_nodes:
                queue.append(src)
                edges_to_export.append({"source": src, "target": tgt, "weight": weight, "label": label})
                
    # Now we have all nodes and internal edges
    nodes_to_export = []
    
    # Fetch full metadata from DB for the visited nodes
    for nid in visited_nodes:
        row = execute_query("SELECT * FROM lgnn_nodes WHERE id = ?", (nid,))
        if row:
            r = row[0]
            nodes_to_export.append({
                "id": r["id"],
                "text_content": r["text_content"],
                "confidence": r["confidence"],
                "source_tag": r["source_tag"],
                "meta_data": json.loads(r["meta_data"]) if r["meta_data"] else {}
            })
            
    bundle = {
        "auratic_app_version": "1.0",
        "app_name": app_name,
        "author": author,
        "root_id": root_id,
        "nodes": nodes_to_export,
        "edges": edges_to_export
    }
    
    bundle_json = json.dumps(bundle, indent=2)
    filename = f"{app_name.replace(' ', '_').lower()}_bundle.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(bundle_json)
        
    logger.info(f"App Bundle exported successfully: {filename} with {len(nodes_to_export)} nodes.")
    return filename

def import_app(filepath: str, inject_into_graph: bool = True):
    """
    Imports an AuraticAppPackage and generates new IDs to prevent collisions,
    effectively creating a localized instance of the app in the graph.
    """
    logger.info(f"Importing App Bundle from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        bundle = json.load(f)
        
    if bundle.get("auratic_app_version") != "1.0":
        logger.warning("Unknown app bundle version.")
        
    id_mapping = {}
    
    # Generate new isolated IDs for this instance of the app
    instance_suffix = str(uuid.uuid4())[:8]
    for n in bundle["nodes"]:
        old_id = n["id"]
        new_id = f"{old_id}_{instance_suffix}"
        id_mapping[old_id] = new_id
        
        if inject_into_graph:
            # We initialize with a zero-tensor for the embedding, it will heal over time
            emb = torch.zeros(128)
            save_node(
                new_id, emb, 0.0,
                confidence=n.get("confidence", 0.5),
                plateau_factor=0.0,
                is_active=True,
                is_pinned=True,  # Apps usually stay pinned
                text_content=n.get("text_content", ""),
                source_tag="community_app",
                meta_data=n.get("meta_data", {})
            )
            
    if inject_into_graph:
        for e in bundle["edges"]:
            old_src, old_tgt = e["source"], e["target"]
            new_src = id_mapping.get(old_src)
            new_tgt = id_mapping.get(old_tgt)
            if new_src and new_tgt:
                save_edge(new_src, new_tgt, e.get("weight", 0.5), label=e.get("label", "app_link"))
                
    logger.info(f"App '{bundle.get('app_name')}' successfully injected. Root is now {id_mapping.get(bundle.get('root_id'))}")
    return id_mapping
