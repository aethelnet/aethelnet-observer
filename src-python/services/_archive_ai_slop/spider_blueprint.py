import os
import ast
import torch
import logging
from pathlib import Path
import sys
import sqlite3
import time

sys.path.append("/home/nikahrlyn/auratic-systems-prime")
from lgnn.database import save_node, save_edge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BlueprintSpider")

class BlueprintSpider:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        
    def parse_file(self, filepath: Path):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            return {
                "name": filepath.name,
                "path": str(filepath),
                "classes": classes,
                "functions": functions,
                "size": len(content)
            }
        except Exception as e:
            return None

    def ingest(self):
        logger.info(f"🕸️ Blueprint Spider ingesting directory: {self.target_dir}")
        
        hub_id = "Hub_Blueprint_Services"
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
                text_content="Auratic Systems Prime - Services Codebase Blueprint Hub",
                source_tag="blueprint",
                node_type="hub"
            )
        except sqlite3.OperationalError as e:
            logger.error(f"DB Lock during Hub insert, skipping for now: {e}")
        
        count = 0
        for py_file in self.target_dir.rglob("*.py"):
            if "venv" in py_file.parts or "__pycache__" in py_file.parts:
                continue
                
            info = self.parse_file(py_file)
            if not info:
                continue
                
            node_id = f"Blueprint_File_{info['name']}"
            text_content = f"File: {info['path']}\nClasses: {', '.join(info['classes'])}\nFunctions: {', '.join(info['functions'])}\nSize: {info['size']} bytes"
            emb = torch.randn(128)
            
            try:
                save_node(
                    node_id=node_id,
                    embedding=emb,
                    mean_activation=float(emb.mean()),
                    confidence=0.9,
                    plateau_factor=0.0,
                    is_grounded=False,
                    help_chain=False,
                    text_content=text_content,
                    source_tag="blueprint",
                    node_type="concept",
                    parent_id=hub_id
                )
                save_edge(hub_id, node_id, weight=0.5, label="contains_module")
                count += 1
                logger.info(f"Successfully injected node: {node_id}")
            except sqlite3.OperationalError as e:
                logger.error(f"DB locked while injecting {node_id}. Retrying...")
                time.sleep(1) # Simple backoff
                
            # Sleep to yield to living_loop
            time.sleep(0.5)
            
        logger.info(f"✅ Ingested {count} Python modules into the LGNN.")

if __name__ == "__main__":
    spider = BlueprintSpider("/home/nikahrlyn/auratic-systems-prime/backend/services")
    spider.ingest()
