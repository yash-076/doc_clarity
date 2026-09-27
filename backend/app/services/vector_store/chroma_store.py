import chromadb
from pathlib import Path
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.services.vector_store.base import VectorStore

class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB implementation of VectorStore."""

    def __init__(self, persist_dir: Path | None = None, collection_name: str | None = None):
        self.persist_dir = (persist_dir or settings.CHROMA_PERSIST_DIRECTORY).resolve()
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Ensure persistence directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Get or create collection using cosine metadata distance
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaVectorStore initialized at {self.persist_dir} (Collection: {self.collection_name})")

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """ChromaDB metadata requires primitive values (str, int, float, bool). Convert None/null to empty str."""
        clean_meta = {}
        for k, v in metadata.items():
            if v is None:
                clean_meta[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)
        return clean_meta

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        if not ids:
            return

        sanitized_metadatas = [self._sanitize_metadata(m) for m in metadatas]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=sanitized_metadatas
        )
        logger.info(f"Added {len(ids)} vector points to Chroma collection '{self.collection_name}'.")

    def search(
        self,
        query_embedding: List[float],
        document_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        target_doc_id = str(document_id)
        
        # Enforce document-level isolation filter
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": target_doc_id},
            include=["documents", "metadatas", "distances"]
        )

        formatted_results: List[Dict[str, Any]] = []
        
        if not results or not results.get("ids") or not results["ids"][0]:
            return formatted_results

        ids_list = results["ids"][0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for i in range(len(ids_list)):
            raw_dist = dists_list[i] if i < len(dists_list) else 0.0
            # Convert cosine distance d to similarity score (1 - d)
            similarity_score = max(0.0, float(1.0 - raw_dist))

            meta = metas_list[i] if i < len(metas_list) else {}
            
            # Restore None values if string was empty
            page_num = meta.get("page_number")
            page_num_val = int(page_num) if page_num != "" and page_num is not None else None
            
            section_val = meta.get("section")
            section_val = section_val if section_val != "" else None

            formatted_results.append({
                "chunk_id": ids_list[i],
                "document_id": meta.get("document_id", target_doc_id),
                "text": docs_list[i] if i < len(docs_list) else "",
                "score": round(similarity_score, 4),
                "page_number": page_num_val,
                "section": section_val,
                "document_type": meta.get("document_type", "other"),
                "extraction_method": meta.get("extraction_method", "text")
            })

        return formatted_results

    def delete_document(self, document_id: str) -> None:
        target_doc_id = str(document_id)
        try:
            self.collection.delete(where={"document_id": target_doc_id})
            logger.info(f"Deleted vector points for document_id={target_doc_id} from Chroma collection.")
        except Exception as e:
            logger.warning(f"Error or no vectors found when deleting document_id={target_doc_id} from Chroma: {str(e)}")

    def get_indexed_count(self, document_id: str) -> int:
        target_doc_id = str(document_id)
        try:
            res = self.collection.get(where={"document_id": target_doc_id}, include=[])
            return len(res.get("ids", []))
        except Exception:
            return 0
