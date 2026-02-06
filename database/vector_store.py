import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

class VectorDB:
    def __init__(self, collection_name: str = "tutorial_chunks"):
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
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_similar(self, query: str, n_results: int = 3) -> List[str]:
        """
        Query for similar documents.
        """
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
        # self.client.delete_collection(self.collection.name)
        # self.collection = self.client.get_or_create_collection(self.collection.name)
        pass

if __name__ == "__main__":
    db = VectorDB()
    # db.add_documents(["doc1", "doc2"], [{"meta": 1}, {"meta": 2}], ["1", "2"])
    # print(db.query_similar("doc1"))
    pass
