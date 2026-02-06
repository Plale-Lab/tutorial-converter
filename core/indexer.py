"""
Document Indexer Service
Scans the RAG database folder and indexes documents into the vector store.
"""
import os
import hashlib
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import VectorDB
from database.vector_store import VectorDB

class DocumentIndexer:
    """
    Indexes documents from a folder into the vector database.
    Supports: PDF, TXT, MD files
    """
    
    def __init__(self, rag_folder: Optional[str] = None):
        self.rag_folder = rag_folder or os.getenv("RAG_FOLDER", "./document/convertit/database")
        self.db = VectorDB(collection_name="rag_knowledge_base")
        self._indexed_hashes: set = set()
        
        # Track what's been indexed to avoid duplicates
        self._load_indexed_hashes()
    
    def _load_indexed_hashes(self):
        """Load previously indexed file hashes (simple persistence)."""
        hash_file = os.path.join(self.rag_folder, ".indexed_hashes")
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r') as f:
                    self._indexed_hashes = set(f.read().strip().split('\n'))
            except Exception:
                self._indexed_hashes = set()
    
    def _save_indexed_hashes(self):
        """Save indexed file hashes."""
        os.makedirs(self.rag_folder, exist_ok=True)
        hash_file = os.path.join(self.rag_folder, ".indexed_hashes")
        with open(hash_file, 'w') as f:
            f.write('\n'.join(self._indexed_hashes))
    
    def _file_hash(self, filepath: str) -> str:
        """Generate a hash for a file based on path + modification time."""
        stat = os.stat(filepath)
        return hashlib.md5(f"{filepath}:{stat.st_mtime}".encode()).hexdigest()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks for better retrieval."""
        chunks = []
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text]
        
        i = 0
        while i < len(words):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        
        return chunks
    
    def _extract_text_from_file(self, filepath: str) -> Optional[str]:
        """Extract text content from supported file types."""
        ext = Path(filepath).suffix.lower()
        
        try:
            if ext == '.txt' or ext == '.md':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif ext == '.pdf':
                # Try to use LlamaParse or fallback to simple extraction
                try:
                    from core.ingestion import IngestionService
                    service = IngestionService()
                    return service.parse_url(filepath)
                except Exception as e:
                    logger.warning(f"PDF extraction failed for {filepath}: {e}")
                    return None
            
            else:
                logger.debug(f"Unsupported file type: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None
    
    def index_folder(self, force_reindex: bool = False) -> Dict[str, int]:
        """
        Scan the RAG folder and index all supported documents.
        
        Returns:
            Dict with counts of files indexed, skipped, and failed.
        """
        stats = {"indexed": 0, "skipped": 0, "failed": 0}
        
        if not os.path.exists(self.rag_folder):
            logger.warning(f"RAG folder does not exist: {self.rag_folder}")
            os.makedirs(self.rag_folder, exist_ok=True)
            return stats
        
        supported_extensions = {'.txt', '.md', '.pdf'}
        
        logger.info(f"Scanning RAG folder: {self.rag_folder}")
        
        for root, dirs, files in os.walk(self.rag_folder):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if filename.startswith('.'):
                    continue
                    
                filepath = os.path.join(root, filename)
                ext = Path(filename).suffix.lower()
                
                if ext not in supported_extensions:
                    continue
                
                file_hash = self._file_hash(filepath)
                
                # Skip if already indexed (unless force)
                if not force_reindex and file_hash in self._indexed_hashes:
                    stats["skipped"] += 1
                    continue
                
                # Extract and index
                logger.info(f"Indexing: {filename}")
                text = self._extract_text_from_file(filepath)
                
                if not text:
                    stats["failed"] += 1
                    continue
                
                # Chunk the text
                chunks = self._chunk_text(text)
                
                # Add to vector DB
                try:
                    relative_path = os.path.relpath(filepath, self.rag_folder)
                    
                    documents = chunks
                    metadatas = [
                        {
                            "source": relative_path,
                            "filename": filename,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "type": "rag_document"
                        }
                        for i in range(len(chunks))
                    ]
                    ids = [f"{file_hash}_chunk_{i}" for i in range(len(chunks))]
                    
                    self.db.add_documents(documents=documents, metadatas=metadatas, ids=ids)
                    
                    self._indexed_hashes.add(file_hash)
                    stats["indexed"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to index {filename}: {e}")
                    stats["failed"] += 1
        
        # Save hashes
        self._save_indexed_hashes()
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    def query_knowledge(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Query the indexed knowledge base for relevant content.
        
        Returns:
            List of dicts with 'content' and 'source' keys.
        """
        results = self.db.query_similar(query, n_results=n_results)
        
        # For now, return simple list of content
        return [{"content": r, "source": "knowledge_base"} for r in results]
    
    def get_indexed_count(self) -> int:
        """Return count of indexed files."""
        return len(self._indexed_hashes)


# Singleton instance for use across the app
_indexer_instance: Optional[DocumentIndexer] = None

def get_indexer() -> DocumentIndexer:
    """Get or create the document indexer singleton."""
    global _indexer_instance
    if _indexer_instance is None:
        _indexer_instance = DocumentIndexer()
    return _indexer_instance

def index_rag_folder_on_startup():
    """Called on app startup to index documents."""
    try:
        indexer = get_indexer()
        stats = indexer.index_folder()
        logger.info(f"Startup indexing: {stats['indexed']} new, {stats['skipped']} cached, {stats['failed']} failed")
        return stats
    except Exception as e:
        logger.error(f"Startup indexing failed: {e}")
        return {"indexed": 0, "skipped": 0, "failed": 0, "error": str(e)}


if __name__ == "__main__":
    # Test indexing
    logging.basicConfig(level=logging.INFO)
    indexer = DocumentIndexer()
    stats = indexer.index_folder()
    print(f"Indexed: {stats}")
