from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from packages.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class KnowledgeDocument:
    """Strongly-typed model for retrieved knowledge."""
    id: str
    content: str
    source_uri: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None

class KnowledgeRetrieval:
    """
    High-level API for retrieving structured knowledge (documents, notes, etc).
    Uses SemanticMemory under the hood but returns strongly-typed models 
    expected by the Planner and Layer 1.
    """
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic = semantic_memory

    async def ingest_document(self, doc_id: str, content: str, source_uri: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Ingests a document into the knowledge base."""
        meta = metadata or {}
        if source_uri:
            meta["source_uri"] = source_uri
        meta["doc_id"] = doc_id
        
        # We store the document as a dict so we can retrieve full context later
        payload = {
            "doc_id": doc_id,
            "content": content,
            "source_uri": source_uri,
            "metadata": meta
        }
        
        await self.semantic.add_knowledge(doc_id, payload, metadata=meta)
        logger.info(f"Ingested document {doc_id} into knowledge base.")

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeDocument]:
        """Retrieves documents matching the query and returns strongly-typed models."""
        raw_results = await self.semantic.search_similar(query, top_k=top_k, metadata_filter=filters)
        
        docs = []
        for res in raw_results:
            if isinstance(res, dict) and "content" in res:
                docs.append(KnowledgeDocument(
                    id=res.get("doc_id", "unknown"),
                    content=res["content"],
                    source_uri=res.get("source_uri"),
                    metadata=res.get("metadata", {}),
                    score=res.get("score")
                ))
            else:
                # Fallback for simple string matches
                docs.append(KnowledgeDocument(
                    id="unknown",
                    content=str(res)
                ))
        return docs
