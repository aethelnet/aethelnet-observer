import os
import time
import random
import logging
import sqlite3
import torch
import json
import sys

sys.path.append("/home/nikahrlyn/auratic-systems-prime")
from lgnn.database import save_node, save_edge, get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetheriaSpider")

class AetheriaSpider:
    """
    Spawns RPG Entities (Monsters, NPCs) from LGNN Entropy and Dissonance.
    If a concept node in the graph becomes too dense or stuck (plateau),
    the Spider crystallizes that concept into a physical Aetheria Monster
    that users must defeat via Topological Shear Combat.
    """
    def __init__(self):
        self.monster_archetypes = [
            ("Data Wraith", "A spectral entity born from fragmented knowledge.", 150, 15),
            ("Syntactic Behemoth", "A brute force anomaly of recursive code.", 400, 30),
            ("Echo Weaver", "A trickster born from redundant semantic loops.", 120, 40),
            ("Null Pointer Leviathan", "A massive void creature consuming memory.", 600, 50),
            ("Rogue Heuristic", "A fast, unpredictable logic demon.", 90, 60)
        ]

    def fetch_dissonant_nodes(self):
        conn = get_db_connection()
        cur = conn.cursor()
        # Find nodes that have high plateau factor (stuck) or high dissonance
        cur.execute("""
            SELECT id, text_content, plateau_factor 
            FROM lgnn_nodes 
            WHERE plateau_factor > 0.5 AND is_deleted = 0
            ORDER BY plateau_factor DESC
            LIMIT 5
        """)
        nodes = cur.fetchall()
        conn.close()
        return nodes

    def spawn_monsters_at_node(self, node):
        source_id = node[0]
        content = node[1]
        plateau = node[2]

        archetype = random.choice(self.monster_archetypes)
        monster_id = f"Entity_{archetype[0].replace(' ', '')}_{int(time.time())}_{random.randint(100,999)}"
        
        hp = int(archetype[2] * (1.0 + plateau))
        atk = int(archetype[3] * (1.0 + plateau))
        
        meta_data = {
            "type": "monster",
            "hp": hp,
            "max_hp": hp,
            "atk": atk,
            "archetype": archetype[0],
            "color": "#ef4444",
            "ui_template": "<h1>Aetheria Threat Detected</h1><p>This entity blocks graph convergence.</p>"
        }

        text_content = f"[{archetype[0]}]\n{archetype[1]}\n\nBorn from the dissonance of node: {source_id}\nHP: {hp} | ATK: {atk}"
        emb = torch.randn(128)
        
        try:
            save_node(
                node_id=monster_id,
                embedding=emb,
                mean_activation=float(emb.mean()),
                confidence=1.0,
                plateau_factor=0.0,
                is_grounded=False,
                help_chain=False,
                text_content=text_content,
                source_tag="aetheria_anomaly",
                meta_data=json.dumps(meta_data)
            )
            logger.info(f"Spawned anomaly '{monster_id}' connected to '{source_id}'")
            
            # Spawn a component (weapon/limb) attached to the boss
            comp_id = f"Comp_{int(time.time())}_{random.randint(100,999)}"
            comp_types = [("Corrupted Blade", 15.0), ("Aetherial Shield", 20.0), ("Void Core", 50.0)]
            comp = random.choice(comp_types)
            
            comp_meta = {
                "type": "component",
                "mass": comp[1],
                "color": "#a855f7",
                "is_severed_loot": False,
                "origin_boss": monster_id
            }
            
            save_node(
                node_id=comp_id,
                embedding=torch.randn(128),
                mean_activation=1.0,
                confidence=1.0,
                plateau_factor=0.0,
                is_grounded=True,
                help_chain=False,
                text_content=f"{comp[0]}\n\nAn anomaly component attached to {archetype[0]}.",
                source_tag="aetheria_component",
                meta_data=json.dumps(comp_meta)
            )
            
            # Link boss to component
            save_edge(monster_id, comp_id, weight=0.9)
            logger.info(f"Spawned component '{comp_id}' attached to '{monster_id}'")

            # Link boss to origin
            save_edge(source_id, monster_id, weight=0.9, label="infected_by")
            
            logger.info(f"🦇 Spawned {archetype[0]} ({monster_id}) with {hp} HP at node {source_id}.")
            return monster_id
        except Exception as e:
            logger.error(f"Failed to spawn monster {monster_id}: {e}")
            return None

    def spawn_monsters(self):
        logger.info("⚔️ Aetheria Spider scanning LGNN for anomalies to crystallize...")
        nodes = self.fetch_dissonant_nodes()
        
        if not nodes:
            logger.info("No major anomalies found. The Aetheria realm is peaceful (for now).")
            nodes = [("random_void", "The empty space between thoughts.", 0.6)]

        for node in nodes:
            self.spawn_monsters_at_node(node)
            time.sleep(0.5)
            
            time.sleep(0.5)

    def run_loop(self):
        while True:
            self.spawn_monsters()
            time.sleep(300) # Scan every 5 minutes

if __name__ == "__main__":
    spider = AetheriaSpider()
    # Just run once for testing if executed directly
    spider.spawn_monsters()
