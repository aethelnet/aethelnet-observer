import os
import sys
import sqlite3
import uuid
import time
import re
import tempfile
import subprocess
import shutil

class CodeSpider:
    """
    LGNN GitRepoVectorizer (CodeSpider)
    Clones a remote GitHub repository and vectorizes its file tree and imports 
    into the LGNN graph as connected concept nodes.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables_if_needed()

    def create_tables_if_needed(self):
        # Ensure base LGNN tables exist (in case this is run independently)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lgnn_nodes (
                id TEXT PRIMARY KEY,
                text_content TEXT,
                node_type TEXT,
                meta_data TEXT,
                parent_id TEXT,
                source_tag TEXT,
                confidence REAL DEFAULT 1.0,
                last_updated REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lgnn_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                target TEXT,
                label TEXT,
                weight REAL DEFAULT 1.0,
                last_updated REAL
            )
        ''')
        self.conn.commit()

    def insert_node(self, node_id, text_content, node_type, parent_id=None, meta_data="{}"):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO lgnn_nodes 
            (id, text_content, node_type, parent_id, source_tag, last_updated, meta_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (node_id, text_content, node_type, parent_id, 'CodeSpider', time.time(), meta_data))
        self.conn.commit()

    def insert_edge(self, source, target, label="CONTAINS", weight=1.0):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO lgnn_edges (source, target, label, weight, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (source, target, label, weight, time.time()))
        self.conn.commit()

    def clone_repo(self, repo_url, target_dir):
        print(f"[*] Spawning CodeSpider to clone {repo_url} ...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, target_dir], check=True)

    def extract_includes(self, file_path, file_content):
        # Naive C++/C include extraction
        # e.g., #include "Dynamics3.h"
        includes = []
        for line in file_content.split('\n'):
            match = re.match(r'^\s*#include\s+["<]([^">]+)[">]', line)
            if match:
                includes.append(match.group(1))
        return includes

    def ingest_repo(self, repo_url):
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_node_id = f"REPO_{repo_name}_{uuid.uuid4().hex[:6]}"
        
        # Inject Root Node
        self.insert_node(repo_node_id, f"Repository: {repo_name}", "GitRepo", meta_data=f'{{"url": "{repo_url}"}}')
        print(f"[+] Created Root Node: {repo_node_id}")

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, repo_name)
            self.clone_repo(repo_url, repo_path)

            file_nodes = {} # filename -> node_id

            # Pass 1: Create nodes for all files
            print("[*] Walking file tree and creating File Nodes...")
            for root, dirs, files in os.walk(repo_path):
                if '.git' in root:
                    continue
                
                for file in files:
                    # Filter out binaries and huge files
                    if not file.endswith(('.h', '.cpp', '.c', '.hpp', '.py', '.js', '.ts', '.md', '.txt')):
                        continue
                        
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    file_node_id = f"FILE_{rel_path.replace('/', '_')}_{uuid.uuid4().hex[:4]}"
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        continue # Skip binary/weird encodings
                    
                    # Store node (truncate content if too large to prevent DB bloat)
                    preview = content[:2000] 
                    self.insert_node(file_node_id, f"File: {rel_path}\n\n{preview}", "GitFile", parent_id=repo_node_id)
                    self.insert_edge(repo_node_id, file_node_id, "CONTAINS")
                    
                    file_nodes[file] = {
                        "id": file_node_id,
                        "path": rel_path,
                        "content": content
                    }

            # Pass 2: Connect dependencies (Edges) based on #includes
            print("[*] Scanning for semantic relationships (Includes/Imports)...")
            for filename, data in file_nodes.items():
                includes = self.extract_includes(data["path"], data["content"])
                for inc in includes:
                    # Find if the included file exists in our node list
                    target_filename = os.path.basename(inc)
                    if target_filename in file_nodes:
                        target_id = file_nodes[target_filename]["id"]
                        self.insert_edge(data["id"], target_id, "DEPENDS_ON", weight=2.0)
                        print(f"    [Edge] {filename} -> {target_filename}")

        print(f"[*] CodeSpider execution complete. Repository {repo_name} vectorized into LGNN.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spider_github.py <github_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    
    # Path to the shared SQLite DB
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "lgnn.db")
    
    spider = CodeSpider(db_path)
    spider.ingest_repo(url)
