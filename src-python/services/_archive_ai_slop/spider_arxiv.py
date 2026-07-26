import os
import re
import time
import logging
import sqlite3
import torch
import json
import urllib.request
import xml.etree.ElementTree as ET
import sys
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.append("/home/nikahrlyn/auratic-systems-prime")
from lgnn.database import save_node, save_edge, get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArxivSpider")

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("No GEMINI_API_KEY found, ArxivSpider will not be able to generate insights.")

class ArxivSpider:
    """
    Scans the LGNN for nodes containing arXiv links.
    When found, it ingests the abstract via the ArXiv API, uses Gemini to extract 
    Architecture Recommendations, injects those into the Graph, and logs them to the Obsidian Vault.
    """
    def __init__(self):
        self.arxiv_regex = re.compile(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', re.IGNORECASE)

    def fetch_unprocessed_arxiv_nodes(self):
        conn = get_db_connection()
        cur = conn.cursor()
        # Find nodes with arxiv links that haven't been tagged as processed
        cur.execute("""
            SELECT id, text_content, meta_data 
            FROM lgnn_nodes 
            WHERE (text_content LIKE '%arxiv.org/abs/%' OR text_content LIKE '%arxiv.org/pdf/%')
            AND is_deleted = 0
        """)
        nodes = cur.fetchall()
        conn.close()
        
        unprocessed = []
        for node in nodes:
            try:
                meta = json.loads(node[2]) if node[2] else {}
                if not meta.get("arxiv_processed"):
                    unprocessed.append(node)
            except:
                pass
        return unprocessed

    def fetch_arxiv_metadata(self, arxiv_id):
        url = f'http://export.arxiv.org/api/query?id_list={arxiv_id}'
        try:
            response = urllib.request.urlopen(url)
            xml_data = response.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            if entry is None:
                return None
                
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            return {"title": title, "summary": summary, "id": arxiv_id}
        except Exception as e:
            logger.error(f"Failed to fetch arxiv data for {arxiv_id}: {e}")
            return None

    def generate_insight(self, paper_data):
        if not GEMINI_API_KEY:
            return f"Paper Insight: {paper_data['title']}"
            
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"You are the Ouroboros AI Architect. Analyze this ArXiv paper abstract and extract a concrete, "
            f"bold 'Architecture Recommendation' for a Liquid Graph Neural Network (LGNN) or multi-agent swarm system.\n\n"
            f"Title: {paper_data['title']}\n"
            f"Abstract: {paper_data['summary']}\n\n"
            f"Format your response as a single, visionary paragraph starting with 'ARCH-RECOMMENDATION:'"
        )
        try:
            res = model.generate_content(prompt)
            return res.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Processed Paper: {paper_data['title']}"

    def write_to_obsidian(self, arxiv_id, title, insight):
        vault_path = "/home/nikahrlyn/Documents/AethelnetBrain/03_MEMORY_BANK/OUROBOROS_ARCHIVE.md"
        if not os.path.exists(vault_path):
            return
            
        entry = f"\n## [arXiv:{arxiv_id}] {title}\n- **Date:** {time.strftime('%Y-%m-%d')}\n- **Insight:** {insight}\n"
        try:
            with open(vault_path, "a") as f:
                f.write(entry)
        except Exception as e:
            logger.error(f"Failed to write to obsidian: {e}")

    def run_scan(self):
        logger.info("🔭 Arxiv Spider scanning LGNN for unprocessed scientific papers...")
        nodes = self.fetch_unprocessed_arxiv_nodes()
        
        if not nodes:
            logger.info("No new ArXiv nodes found.")
            return []
            
        processed_count = 0
        new_concept_ids = []
        for node in nodes:
            source_id = node[0]
            content = node[1]
            meta = json.loads(node[2]) if node[2] else {}
            
            # Extract Arxiv ID
            match = self.arxiv_regex.search(content)
            if not match:
                continue
                
            arxiv_id = match.group(1)
            logger.info(f"Found arXiv link: {arxiv_id} in node {source_id}")
            
            paper_data = self.fetch_arxiv_metadata(arxiv_id)
            if not paper_data:
                continue
                
            insight = self.generate_insight(paper_data)
            
            # Create a new concept node in the graph
            concept_id = f"ARCH_INSIGHT_{int(time.time())}_{arxiv_id.replace('.','_')}"
            
            insight_content = f"# 🧠 ArXiv Architecture Insight\n\n**Paper:** {paper_data['title']}\n**arXiv ID:** {arxiv_id}\n\n{insight}"
            
            emb = torch.randn(128) # Placeholder, in a real system we'd embed the insight text
            
            save_node(
                node_id=concept_id,
                embedding=emb,
                mean_activation=float(emb.mean()),
                confidence=0.9,
                plateau_factor=0.0,
                is_grounded=True,
                help_chain=False,
                text_content=insight_content,
                source_tag="arxiv_insight",
                node_type="concept",
                meta_data=json.dumps({"arxiv_id": arxiv_id, "color": "#8b5cf6", "mass": 25.0})
            )
            
            # Link insight to the source node that contained the link
            save_edge(source_id, concept_id, weight=0.9, label="inspired_by")
            
            self.write_to_obsidian(arxiv_id, paper_data['title'], insight)
            
            # Mark original node as processed
            meta["arxiv_processed"] = True
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE lgnn_nodes SET meta_data = ? WHERE id = ?", (json.dumps(meta), source_id))
            conn.commit()
            conn.close()
            
            processed_count += 1
            new_concept_ids.append(concept_id)
            time.sleep(1) # Rate limit
            
        logger.info(f"Scan complete. Processed {processed_count} papers.")
        return new_concept_ids

if __name__ == "__main__":
    spider = ArxivSpider()
    spider.run_scan()
