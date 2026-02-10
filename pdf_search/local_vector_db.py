"""Local Vector Database using Qdrant (In-Memory/File)."""
import os
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config

class LocalVectorDB:
    """Local vector database wrapper for Qdrant."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        # Use a local file path for persistence on Render (if disk is writable)
        # or in-memory for ephemeral instances.
        # Ideally, Render Disk should be mounted at /data or similar if paid.
        # For free tier, we use a local directory which is ephemeral but survives restarts until redeploy.
        self.db_path = Config.PROJECT_ROOT / "qdrant_data"
        self.db_path.mkdir(exist_ok=True)
        
        print(f"Initializing Qdrant at {self.db_path}")
        self.client = QdrantClient(location=":memory:")
        self.collection_name = Config.COLLECTION_NAME
        
    def create_collection(self, dimension: int = 384) -> bool:
        """Create a new collection."""
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            return True
        except Exception as e:
            print(f"Error creating Qdrant collection: {e}")
            return False

    def insert_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> bool:
        """Insert vectors into the collection."""
        points = []
        for i, vec in enumerate(vectors):
            # Use chunk_id or index as ID
            import uuid
            point_id = str(uuid.uuid4())
            
            # Metadata clean up (ensure serialization)
            meta = metadata[i].copy()
            
            points.append(PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload=meta
            ))
        
        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        return True

    def search(self, query_vector: np.ndarray, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_filter = None
        if filter_dict:
            conditions = []
            for key, val in filter_dict.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=val)))
            query_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            query_filter=query_filter,
            limit=top_k
        )
        
        # Format results to match Endee format
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "id": hit.id,
                "score": hit.score,
                "metadata": hit.payload
            })
        
        return formatted_results

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection info."""
        try:
            return self.client.get_collection(self.collection_name).dict()
        except:
            return {}
            
    def delete_collection(self) -> bool:
        """Delete collection."""
        try:
            self.client.delete_collection(self.collection_name)
            return True
        except:
            return False
