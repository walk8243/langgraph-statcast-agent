"""Qdrant vector store management for Text-to-SQL knowledge."""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any, Dict, List, Optional

from google import genai
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_DIMENSION = 3072


class QdrantKnowledgeStore:
    """Manages storage and vector search of DDLs, documentation, and SQL samples in Qdrant."""

    def __init__(
        self,
        url: Optional[str] = None,
        collection_name: Optional[str] = None,
        api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        dimension: int = DEFAULT_DIMENSION,
    ):
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection_name
        self.api_key = api_key
        self.gemini_api_key = gemini_api_key if gemini_api_key is not None else settings.gemini_api_key
        self.dimension = dimension

        self.client = QdrantClient(url=self.url, api_key=self.api_key, check_compatibility=False)
        self._gemini_client: Optional[genai.Client] = None
        if self.gemini_api_key:
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client for embeddings: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector using Gemini or fallback to deterministic vector."""
        if self._gemini_client:
            try:
                res = self._gemini_client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=text,
                )
                if res and res.embeddings:
                    values = res.embeddings[0].values
                    if len(values) == self.dimension:
                        return values
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed ({e}), using fallback vector")

        # Deterministic fallback embedding for testing / offline
        import numpy as np

        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def ensure_collection(self) -> None:
        """Create Qdrant collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' (dim={self.dimension})")
        except Exception as e:
            logger.error(f"Error checking/creating collection '{self.collection_name}': {e}")
            raise

    def add_ddl(self, table_name: str, ddl: str) -> str:
        """Add table DDL to vector store."""
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ddl:{table_name}"))
        text = f"Table: {table_name}\nSchema DDL:\n{ddl}"
        vector = self.generate_embedding(text)
        payload = {
            "type": "ddl",
            "table_name": table_name,
            "content": ddl,
            "searchable_text": text,
        }
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

    def add_documentation(self, title: str, content: str) -> str:
        """Add documentation / glossary to vector store."""
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"doc:{title}"))
        text = f"Documentation: {title}\n{content}"
        vector = self.generate_embedding(text)
        payload = {
            "type": "doc",
            "title": title,
            "content": content,
            "searchable_text": text,
        }
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

    def add_sql_example(self, question: str, sql: str) -> str:
        """Add a Question-SQL pair to vector store."""
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"sql:{question}"))
        text = f"Question: {question}\nSQL Query:\n{sql}"
        vector = self.generate_embedding(text)
        payload = {
            "type": "sql_example",
            "question": question,
            "sql": sql,
            "content": sql,
            "searchable_text": text,
        }
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

    def search(
        self,
        query: str,
        limit: int = 5,
        item_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search relevant knowledge in Qdrant.

        Args:
            query: Natural language query string.
            limit: Number of results to return.
            item_type: Optional filter by 'ddl', 'doc', or 'sql_example'.

        Returns:
            List of matching items with payload and score.
        """
        self.ensure_collection()
        query_vector = self.generate_embedding(query)

        query_filter = None
        if item_type:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=item_type),
                    )
                ]
            )

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        results = []
        for hit in search_result.points:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            })
        return results

    def get_all_ddls(self) -> List[Dict[str, Any]]:
        """Fetch all stored DDL entries."""
        self.ensure_collection()
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="type", match=MatchValue(value="ddl"))]
            ),
            limit=100,
            with_payload=True,
        )
        return [r.payload for r in records if r.payload]

    def count(self) -> int:
        """Return total count of points in collection."""
        try:
            res = self.client.count(collection_name=self.collection_name)
            return res.count
        except Exception:
            return 0
