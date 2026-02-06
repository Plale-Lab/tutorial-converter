import os
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except Exception as e:
    print(f"WARNING: ChromaDB not available ({e}). Using Mock VectorDB.")
    CHROMA_AVAILABLE = False

class VectorDB:
    def __init__(self, collection_name: str = "tutorial_chunks"):
        if not CHROMA_AVAILABLE:
            return

        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Initialize Client
        # PersistentClient is preferred for local storage
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Add documents to the vector store.
        """
        if not CHROMA_AVAILABLE:
            return

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_similar(self, query: str, n_results: int = 3) -> List[str]:
        """
        Query for similar documents.
        """
        if not CHROMA_AVAILABLE:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Flatten results list (list of lists)
        return results['documents'][0] if results['documents'] else []

    def clear(self):
        """
        Deletes the collection (useful for testing or reset)
        """
        pass

if __name__ == "__main__":
    db = VectorDB()
    pass
