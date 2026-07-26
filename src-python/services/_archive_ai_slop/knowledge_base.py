"""
Knowledge Base Database Service
SQLite-backed block storage with Logseq-style block-level linking.

Single Source of Truth: Database is master, files are rendered views.
"""

import os
import re
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Project root relative database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge.db")


@dataclass
class Block:
    """A single block of content (paragraph, heading, task, code)."""
    id: str
    file_path: Optional[str]  # Source file (None if created directly)
    parent_id: Optional[str]  # Parent block ID for nesting
    content: str              # Raw markdown content
    heading_level: int        # 0=paragraph, 1-6=headings
    block_type: str           # 'text', 'task', 'code', 'heading', 'snippet'
    refs: List[str]           # Outgoing [[links]] and #tags
    backrefs: List[str]       # Incoming links (computed)
    metadata: Dict            # Arbitrary JSON data
    created_at: str
    updated_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeBase:
    """
    SQLite-backed knowledge base with block-level granularity.
    
    Design Principles:
    - Database is the Single Source of Truth (SSOT)
    - Files are rendered views, not the master copy
    - Block-level linking enables Logseq-style references
    - Full-text search across all content
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._init_db()
        self._migrate_db()

    def _migrate_db(self):
        """Apply migrations if needed."""
        with self._conn() as conn:
            # Check for metadata column
            try:
                conn.execute("SELECT metadata FROM blocks LIMIT 1")
            except sqlite3.OperationalError:
                # Column missing, add it
                conn.execute("ALTER TABLE blocks ADD COLUMN metadata TEXT DEFAULT '{}'")
    
    @contextmanager
    def _conn(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    id TEXT PRIMARY KEY,
                    file_path TEXT,
                    parent_id TEXT,
                    content TEXT NOT NULL,
                    heading_level INTEGER DEFAULT 0,
                    block_type TEXT DEFAULT 'text',
                    refs TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (parent_id) REFERENCES blocks(id)
                )
            """)
            
            # Full-text search virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS blocks_fts 
                USING fts5(id, content, block_type)
            """)
            
            # Links table for efficient backref queries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    source_id TEXT,
                    target_id TEXT,
                    link_type TEXT DEFAULT 'ref',
                    PRIMARY KEY (source_id, target_id),
                    FOREIGN KEY (source_id) REFERENCES blocks(id),
                    FOREIGN KEY (target_id) REFERENCES blocks(id)
                )
            """)
            
            # Snippets registry (blocks that are reusable components)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    block_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    inputs TEXT DEFAULT '[]',
                    outputs TEXT DEFAULT '[]',
                    complexity INTEGER DEFAULT 1,
                    FOREIGN KEY (block_id) REFERENCES blocks(id)
                )
            """)

            # Node Islands / Presets (Saved configurations of connected snippets)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    config TEXT NOT NULL, -- JSON graph definition
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _generate_id(self, content: str) -> str:
        """Generate deterministic ID from content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _extract_refs(self, content: str) -> List[str]:
        """Extract [[wikilinks]] and #tags from content."""
        refs = []
        # [[wikilinks]]
        refs.extend(re.findall(r'\[\[([^\]]+)\]\]', content))
        # #tags
        refs.extend(re.findall(r'#(\w+)', content))
        return list(set(refs))
    
    def _detect_block_type(self, content: str) -> str:
        """Detect block type from content."""
        stripped = content.strip()
        
        if stripped.startswith('```'):
            return 'code'
        if stripped.startswith('#'):
            return 'heading'
        if re.match(r'^- \[[x ]\]', stripped):
            return 'task'
        return 'text'
    
    def _detect_heading_level(self, content: str) -> int:
        """Detect heading level (0 for non-headings)."""
        match = re.match(r'^(#{1,6})\s', content.strip())
        if match:
            return len(match.group(1))
        return 0
    
    # ==========================================
    # CRUD Operations
    # ==========================================
    
    def create_block(
        self, 
        content: str, 
        file_path: str = None,
        parent_id: str = None,
        block_type: str = None,
        metadata: Dict = None
    ) -> Block:
        """Create a new block."""
        block_id = self._generate_id(content + str(datetime.now()))
        refs = self._extract_refs(content)
        detected_type = block_type or self._detect_block_type(content)
        heading_level = self._detect_heading_level(content)
        now = datetime.utcnow().isoformat()
        
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO blocks (id, file_path, parent_id, content, heading_level, block_type, refs, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (block_id, file_path, parent_id, content, heading_level, detected_type, json.dumps(refs), json.dumps(metadata or {}), now, now))
            
            # Update FTS index
            conn.execute("""
                INSERT INTO blocks_fts (id, content, block_type)
                VALUES (?, ?, ?)
            """, (block_id, content, detected_type))
        
        return Block(
            id=block_id,
            file_path=file_path,
            parent_id=parent_id,
            content=content,
            heading_level=heading_level,
            block_type=detected_type,
            refs=refs,
            backrefs=[],
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )
    
    def get_block(self, block_id: str) -> Optional[Block]:
        """Get a block by ID with backrefs."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM blocks WHERE id = ?", (block_id,)).fetchone()
            if not row:
                return None
            
            # Get backrefs
            backrefs = [r['source_id'] for r in conn.execute(
                "SELECT source_id FROM links WHERE target_id = ?", (block_id,)
            ).fetchall()]
            
            return Block(
                id=row['id'],
                file_path=row['file_path'],
                parent_id=row['parent_id'],
                content=row['content'],
                heading_level=row['heading_level'],
                block_type=row['block_type'],
                refs=json.loads(row['refs']),
                backrefs=backrefs,
                metadata=json.loads(row['metadata'] if 'metadata' in row.keys() else '{}'), # Use keys() for Row
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    def update_block(self, block_id: str, content: str) -> Optional[Block]:
        """Update a block's content."""
        refs = self._extract_refs(content)
        block_type = self._detect_block_type(content)
        heading_level = self._detect_heading_level(content)
        now = datetime.utcnow().isoformat()
        
        with self._conn() as conn:
            conn.execute("""
                UPDATE blocks SET content = ?, refs = ?, block_type = ?, heading_level = ?, updated_at = ?
                WHERE id = ?
            """, (content, json.dumps(refs), block_type, heading_level, now, block_id))
            
            # Update FTS
            conn.execute("DELETE FROM blocks_fts WHERE id = ?", (block_id,))
            conn.execute("""
                INSERT INTO blocks_fts (id, content, block_type)
                VALUES (?, ?, ?)
            """, (block_id, content, block_type))
        
        return self.get_block(block_id)
    
    def delete_block(self, block_id: str) -> bool:
        """Delete a block (SSOT - single delete point)."""
        with self._conn() as conn:
            # Delete from all tables
            conn.execute("DELETE FROM links WHERE source_id = ? OR target_id = ?", (block_id, block_id))
            conn.execute("DELETE FROM snippets WHERE block_id = ?", (block_id,))
            conn.execute("DELETE FROM blocks_fts WHERE id = ?", (block_id,))
            conn.execute("DELETE FROM blocks WHERE id = ?", (block_id,))
        return True
    
    # ==========================================
    # Search & Query
    # ==========================================
    
    def search(self, query: str, limit: int = 50) -> List[Block]:
        """Full-text search across all blocks."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT b.* FROM blocks b
                JOIN blocks_fts fts ON b.id = fts.id
                WHERE blocks_fts MATCH ?
                LIMIT ?
            """, (query, limit)).fetchall()
            
            return [Block(
                id=r['id'],
                file_path=r['file_path'],
                parent_id=r['parent_id'],
                content=r['content'],
                heading_level=r['heading_level'],
                block_type=r['block_type'],
                refs=json.loads(r['refs']),
                backrefs=[],
                created_at=r['created_at'],
                updated_at=r['updated_at']
            ) for r in rows]
    
    def get_graph(self) -> Dict:
        """Get D3-compatible node/link graph."""
        nodes = []
        links = []
        
        with self._conn() as conn:
            # Get all blocks as nodes
            blocks = conn.execute("SELECT id, content, block_type, heading_level FROM blocks").fetchall()
            for b in blocks:
                nodes.append({
                    "id": b['id'],
                    "label": b['content'][:50] + "..." if len(b['content']) > 50 else b['content'],
                    "type": b['block_type'],
                    "group": b['heading_level']
                })
            
            # Get all links
            link_rows = conn.execute("SELECT source_id, target_id, link_type FROM links").fetchall()
            for l in link_rows:
                links.append({
                    "source": l['source_id'],
                    "target": l['target_id'],
                    "type": l['link_type']
                })
        
        return {"nodes": nodes, "links": links}
    
    # ==========================================
    # File Ingestion
    # ==========================================
    
    def ingest_file(self, file_path: str) -> List[Block]:
        """Parse a markdown file into blocks."""
        if not os.path.isfile(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split into blocks (on double newlines or headings)
        raw_blocks = re.split(r'\n\n+|(?=^#{1,6}\s)', content, flags=re.MULTILINE)
        
        created = []
        parent_id = None
        
        for raw in raw_blocks:
            raw = raw.strip()
            if not raw:
                continue
            
            block = self.create_block(raw, file_path=file_path, parent_id=parent_id)
            created.append(block)
            
            # Track parent for nesting (headings become parents)
            if block.heading_level > 0:
                parent_id = block.id
        
        return created
    
    def ingest_directory(self, directory: str, extensions: List[str] = ['.md']) -> int:
        """Ingest all matching files from a directory."""
        count = 0
        for root, dirs, files in os.walk(directory):
            # Skip hidden/ignored dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv']]
            
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    path = os.path.join(root, f)
                    blocks = self.ingest_file(path)
                    count += len(blocks)
        
        return count
    
    # ==========================================
    # Snippet Integration
    # ==========================================
    
    def register_as_snippet(
        self, 
        block_id: str, 
        name: str, 
        category: str = None,
        inputs: List[str] = None,
        outputs: List[str] = None,
        complexity: int = 1
    ) -> bool:
        """Register a block as a reusable snippet."""
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO snippets (block_id, name, category, inputs, outputs, complexity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (block_id, name, category, json.dumps(inputs or []), json.dumps(outputs or []), complexity))
        return True
    
    def get_snippets(self, category: str = None) -> List[Dict]:
        """Get all registered snippets."""
        with self._conn() as conn:
            if category:
                rows = conn.execute("""
                    SELECT s.*, b.content FROM snippets s
                    JOIN blocks b ON s.block_id = b.id
                    WHERE s.category = ?
                """, (category,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT s.*, b.content FROM snippets s
                    JOIN blocks b ON s.block_id = b.id
                """).fetchall()
            
            return [{
                "block_id": r['block_id'],
                "name": r['name'],
                "category": r['category'],
                "inputs": json.loads(r['inputs']),
                "outputs": json.loads(r['outputs']),
                "complexity": r['complexity'] if 'complexity' in r.keys() else 1,
                "content": r['content']
            } for r in rows]

    def save_preset(self, name: str, config: Dict, description: str = None) -> str:
        """Save a Node Island configuration."""
        preset_id = f"island_{hashlib.sha256((name + str(datetime.now())).encode()).hexdigest()[:8]}"
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO presets (id, name, description, config)
                VALUES (?, ?, ?, ?)
            """, (preset_id, name, description, json.dumps(config)))
        return preset_id

    def get_preset(self, preset_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM presets WHERE id = ?", (preset_id,)).fetchone()
            if row:
                return {
                    "id": row['id'],
                    "name": row['name'],
                    "description": row['description'],
                    "config": json.loads(row['config']),
                    "created_at": row['created_at']
                }
        return None

    def list_presets(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT id, name, description, created_at FROM presets ORDER BY created_at DESC").fetchall()
            return [{
                "id": r['id'],
                "name": r['name'],
                "description": r['description'],
                "created_at": r['created_at']
            } for r in rows]


# Singleton
_kb_instance: Optional[KnowledgeBase] = None

def get_knowledge_base() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
