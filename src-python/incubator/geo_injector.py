import sqlite3
import json
import uuid
import os
import struct
from datetime import datetime

def inject_geo_anchor(conn, label, lat, lng, altitude=0.0, node_type="geo_anchor", content=""):
    node_id = f"{label.replace(' ', '_')}_{uuid.uuid4().hex[:4]}"
    now = datetime.utcnow().isoformat()
    
    meta_data = {
        "spatial": {
            "lat": lat,
            "lng": lng,
            "altitude": altitude,
            "projection": "EPSG:4326"
        },
        "color": "#10b981", # Emerald Green for Geo
        "is_shielded": True # Protect anchors from ODE decay
    }
    
    fake_embedding = struct.pack('f' * 384, *([0.0]*384))
    
    query = """
    INSERT INTO lgnn_nodes (id, embedding, text_content, node_type, source_tag, confidence, parent_id, x, y, meta_data, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO NOTHING
    """
    
    cursor = conn.cursor()
    cursor.execute(
        query,
        (node_id, fake_embedding, content, node_type, "geo", 1.0, "ROOT",
        0.0, 0.0, json.dumps(meta_data), now)
    )
    
    print(f"[+] Injected Geo-Anchor: {label} [{node_id}] at ({lat}, {lng})")
    return node_id

def main():
    db_path = os.path.join(os.path.dirname(__file__), "..", "lgnn.db")
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    
    try:
        # Example 1: Headquarters / Origin Point
        origin_id = inject_geo_anchor(
            conn, 
            label="Aethelburg Alpha Site", 
            lat=52.5200, 
            lng=13.4050, 
            content="Primary Node. Hub for Aethelnet architecture. Local mesh networks synchronize here."
        )
        
        # Example 2: Data Source (e.g. EOS Landviewer / Niantic scan cluster)
        niantic_id = inject_geo_anchor(
            conn,
            label="Niantic Voxel Cluster 7",
            lat=52.5210,
            lng=13.4065,
            content="Aggregated photogrammetry data. 3D point cloud available."
        )
        
        # Edge connecting them: "Spatial proximity" or "Data flow"
        now = datetime.utcnow().isoformat()
        edge_query = """
        INSERT INTO lgnn_edges (source, target, weight, label, is_manual, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, target) DO NOTHING
        """
        cursor = conn.cursor()
        cursor.execute(
            edge_query,
            (niantic_id, origin_id, 1.0, "provides 3D context", True, now)
        )
        print(f"[+] Connected {niantic_id} -> {origin_id}")
        
        conn.commit()

    finally:
        conn.close()
        print("World Model seed complete.")

if __name__ == "__main__":
    main()
