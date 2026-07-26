import os
import torch
import logging
import sys
import time
import sqlite3

sys.path.append("/home/nikahrlyn/auratic-systems-prime")
from lgnn.database import save_node, save_edge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeoSpider")

class GeoSpider:
    """
    [The Eye]
    Ingests physical world anchors, geodata, and spatial coordinates into the LGNN.
    Prepares the graph for Niantic 3D-Photogrammetry and EOS Landviewer satellite streams.
    """
    def __init__(self):
        # Mocked foundational spatial data to anchor the World Model
        self.spatial_anchors = [
            {
                "id": "Geo_Server_141",
                "label": "Physical Server 141 Location",
                "lat": 50.1109, "lon": 8.6821, # Frankfurt roughly
                "type": "datacenter_anchor",
                "content": "Physical hosting site for LGNN Core. Hardware nexus."
            },
            {
                "id": "Geo_Grid_Prime",
                "label": "Prime Meridian Anchor",
                "lat": 51.4779, "lon": 0.0015, # Greenwich
                "type": "global_grid_node",
                "content": "Global absolute positioning baseline (0,0,0) for the LGNN spatial grid."
            },
            {
                "id": "Geo_Niantic_Scan_01",
                "label": "Niantic VPS Scaffold",
                "lat": 37.7749, "lon": -122.4194, # SF
                "type": "photogrammetry_mesh",
                "content": "Aetheria AR mapping anchor. Linked to Niantic Lightship VPS for spatial persistence."
            },
            {
                "id": "Geo_EOS_Sat_Feed",
                "label": "EOS Landviewer Downlink",
                "lat": 48.1351, "lon": 11.5820, # Munich
                "type": "satellite_telemetry",
                "content": "Live macro-spectral land view feed. Analyzes global vegetation and heat signatures."
            }
        ]

    def ingest(self):
        logger.info("👁️ Geo Spider initializing The Eye (World Model Anchors)...")
        
        hub_id = "Hub_TheEye"
        hub_emb = torch.randn(128)
        
        try:
            save_node(
                node_id=hub_id,
                embedding=hub_emb,
                mean_activation=float(hub_emb.mean()),
                confidence=1.0,
                plateau_factor=0.0,
                is_grounded=True,
                help_chain=False,
                text_content="Auratic World Model Hub - Physical Space & Geo-Telemetry",
                source_tag="geo_location",
                node_type="hub"
            )
            logger.info("Created Hub_TheEye.")
        except sqlite3.OperationalError as e:
            logger.error(f"DB Lock during Hub insert: {e}")
            
        for anchor in self.spatial_anchors:
            node_id = anchor["id"]
            text_content = f"Label: {anchor['label']}\nLat/Lon: {anchor['lat']}, {anchor['lon']}\nType: {anchor['type']}\n\n{anchor['content']}"
            emb = torch.randn(128)
            
            try:
                save_node(
                    node_id=node_id,
                    embedding=emb,
                    mean_activation=float(emb.mean()),
                    confidence=0.9,
                    plateau_factor=0.0,
                    is_grounded=True, # Geo nodes are highly grounded by definition
                    help_chain=False,
                    text_content=text_content,
                    source_tag="geo_location",
                    node_type="geo_anchor",
                    parent_id=hub_id
                )
                save_edge(hub_id, node_id, weight=0.8, label="spatial_link")
                logger.info(f"Successfully pinned spatial anchor: {node_id}")
            except sqlite3.OperationalError as e:
                logger.error(f"DB locked while injecting {node_id}. Retrying...")
                time.sleep(1)
            
            time.sleep(0.5)
            
        logger.info("✅ The Eye is open. Spatial anchors injected into the LGNN.")

if __name__ == "__main__":
    spider = GeoSpider()
    spider.ingest()
