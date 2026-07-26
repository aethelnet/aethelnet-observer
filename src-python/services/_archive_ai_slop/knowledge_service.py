
import os
import glob
import logging
import pickle
import numpy as np
from typing import List, Dict, Tuple
from functools import lru_cache

# We use sklearn for a robust, dependency-light MVP.
# If unavailable, we'll fail gracefully or implement a naive match.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from config.settings import get_settings

logger = logging.getLogger("KnowledgeService")

class KnowledgeService:
    """
    The Librarian.
    Ingests text from 'backend/data/vault', chunks it, and provides
    semantic search capabilities using TF-IDF (default) or Embeddings (future).
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # CORRECT PATHING: The vault is source code (static), not persistent data.
        # Calculate relative to THIS file (backend/services/knowledge_service.py)
        # Go up one level to 'backend', then down to 'data/vault'
        current_dir = os.path.dirname(os.path.abspath(__file__)) # backend/services
        backend_dir = os.path.dirname(current_dir) # backend
        self.vault_path = os.path.join(backend_dir, "data", "vault")
        
        self.index_path = self.settings.KNOWLEDGE_STORE_PATH
        
        # State
        self.documents: List[Dict] = [] # [{'content': str, 'source': str, 'id': int}]
        self.vectorizer = None # TfidfVectorizer
        self.tfidf_matrix = None # Sparse matrix
        
        # Ensure vault exists
        os.makedirs(self.vault_path, exist_ok=True)
        
        # Load index if exists
        self.load_index()

    def ingest_vault(self, force_rebuild: bool = False):
        """
        Scans the vault for .md and .txt files, chunks them, and rebuilds index.
        """
        logger.info(f"Scanning vault at: {self.vault_path}")
        
        # 1. Gather Files
        files = glob.glob(os.path.join(self.vault_path, "**/*.md"), recursive=True)
        files += glob.glob(os.path.join(self.vault_path, "**/*.txt"), recursive=True)
        
        if not files:
            logger.warning("No documents found in vault.")
            return

        new_docs = []
        doc_id_counter = 0
        
        # 2. Process Files
        for fpath in files:
            try:
                base_name = os.path.basename(fpath)
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Improved Chunking: Split by Markdown Headers to keep context together
                import re
                sections = re.split(r'\n(##?#? .*)', content)
                
                current_header = ""
                for section in sections:
                    if not section.strip(): continue
                    
                    if section.startswith('#'):
                        current_header = section.strip()
                        continue
                        
                    # Combine header with content for better search indexing
                    chunk_content = f"{current_header}\n{section.strip()}" if current_header else section.strip()
                    
                    if len(chunk_content) < 30: continue
                    
                    new_docs.append({
                        'id': doc_id_counter,
                        'content': chunk_content,
                        'source': base_name,
                        'full_path': fpath
                    })
                    doc_id_counter += 1
                    
            except Exception as e:
                logger.error(f"Failed to read {fpath}: {e}")
                
        self.documents = new_docs
        logger.info(f"Ingested {len(self.documents)} snippets from {len(files)} files.")
        
        # 3. Build Index
        self.build_index()
        
    def build_index(self):
        """
        Creates the TF-IDF matrix from self.documents.
        """
        if not self.documents:
            return

        if not HAS_SKLEARN:
            logger.warning("sklearn not found. Semantic search disabled (Index not built).")
            return

        try:
            logger.info("Building TF-IDF Index...")
            texts = [d['content'] for d in self.documents]
            
            # Stop words english, unigrams + bigrams for better context capture
            self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            logger.info(f"Index built. Shape: {self.tfidf_matrix.shape}")
            self.save_index()
            
        except Exception as e:
            logger.error(f"Index build failed: {e}")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Semantic search for the query provided.
        Returns list of matched document chunks with scores.
        """
        if not self.documents:
            return []
            
        # Fallback if no sklearn (Naive keyword match)
        if not HAS_SKLEARN or self.vectorizer is None:
            return self._naive_search(query, top_k)
            
        try:
            # Transform query
            query_vec = self.vectorizer.transform([query])
            
            # Cosine Similarity
            cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Get Top K indices
            # argsort sorts ascending, so we take last k and reverse
            related_docs_indices = cosine_sim.argsort()[:-top_k-1:-1]
            
            results = []
            for idx in related_docs_indices:
                score = cosine_sim[idx]
                if score < 0.1: continue # Filter noise
                
                doc = self.documents[idx].copy()
                doc['score'] = float(score)
                results.append(doc)
                
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _naive_search(self, query: str, top_k: int) -> List[Dict]:
        """Simple case-insensitive substring match."""
        results = []
        q_lower = query.lower()
        for doc in self.documents:
            if q_lower in doc['content'].lower():
                d = doc.copy()
                d['score'] = 1.0
                results.append(d)
                if len(results) >= top_k: break
        return results

    def save_index(self):
        """Persist index to disk."""
        try:
            with open(self.index_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'vectorizer': self.vectorizer,
                    'tfidf_matrix': self.tfidf_matrix
                }, f)
            logger.info("Index saved to disk.")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def load_index(self):
        """Load index from disk."""
        if not os.path.exists(self.index_path):
            return
            
        try:
            with open(self.index_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.vectorizer = data.get('vectorizer')
                self.tfidf_matrix = data.get('tfidf_matrix')
            logger.info(f"Loaded index with {len(self.documents)} documents.")
        except Exception as e:
            logger.warning(f"Failed to load index (will rebuild): {e}")

@lru_cache()
def get_knowledge_service():
    return KnowledgeService()
