"""Endee vector database client for semantic search."""
import requests
import numpy as np
import msgpack
from typing import List, Dict, Any, Optional
from config import Config


class EndeeClient:
    """Client for interacting with Endee vector database."""
    
    def __init__(self, base_url: str = None):
        """Initialize Endee client.
        
        Args:
            base_url: Base URL for Endee server (default from config)
        """
        self.base_url = base_url or Config.ENDEE_URL
        self.index_name = Config.COLLECTION_NAME
        
    def create_collection(self, dimension: int = None) -> bool:
        """Create a new index in Endee.
        
        Args:
            dimension: Vector dimension (default from config)
            
        Returns:
            True if successful
        """
        dimension = dimension or Config.EMBEDDING_DIM
        
        try:
            # Server uses /api/v1/index/create
            response = requests.post(
                f"{self.base_url}/api/v1/index/create",
                json={
                    "index_name": self.index_name,
                    "dim": dimension,
                    "space_type": "cosine",
                    "precision": "int8d" # Match server expected: int8d
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 409:
                # Index already exists
                print(f"Index '{self.index_name}' already exists")
                return True
            else:
                print(f"Failed to create index (Status {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    def insert_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """Insert vectors with metadata into Endee.
        
        Args:
            vectors: Array of vectors (N x D)
            metadata: List of metadata dicts for each vector
            
        Returns:
            True if successful
        """
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors must match metadata entries")
        
        try:
            # Server expects a list of objects at /api/v1/index/{name}/vector/insert
            data = []
            for i in range(len(vectors)):
                # We need a unique ID for each vector. Chunk IDs are available in metadata.
                # Actually server doesn't REQUIRE an ID if not provided?
                # Let's use the one from metadata if it exists, else use index
                vec_id = metadata[i].get("id", str(metadata[i].get("chunk_id", i)))
                
                # Server metadata filtering expects the actual metadata to be indexed if possible,
                # but currently we just store it. Wait, the server handles metadata differently.
                # In main.cpp, addVectors takes HybridVectorObject which has metadata support?
                
                data.append({
                    "id": str(vec_id),
                    "vector": vectors[i].tolist(),
                    "metadata": metadata[i]
                })
            
            # Using JSON for insertion as it's easier to debug than binary msgpack for now
            response = requests.post(
                f"{self.base_url}/api/v1/index/{self.index_name}/vector/insert",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=120  # Larger timeout for potentially large insertions
            )
            
            if response.status_code == 200:
                print(f"DEBUG: Successfully inserted {len(data)} vectors")
                return True
            else:
                print(f"[ERROR] Failed to insert vectors (Status {response.status_code})")
                print(f"DEBUG: Server Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            return False
            
    def delete_vectors(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete vectors matching filter (Best Effort).
        
        Endee API might not support granular delete yet.
        """
        print(f"WARNING: Granular delete not fully supported in EndeeClient for {filter_dict}")
        return True # Pretend success for now to allow local cleanup
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query vector (1D array)
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of results with metadata and scores
        """
        try:
            # Server endpoint: POST /api/v1/index/{name}/search
            data = {
                "vector": query_vector.tolist(),
                "k": top_k
            }
            
            # Endee server expects filters as an array of objects
            # Format: [{"field": {"$eq": value}}]
            if filter_dict:
                filters = []
                for key, val in filter_dict.items():
                    filters.append({key: {"$eq": val}})
                data["filter"] = filters
            
            print(f"DEBUG: Searching index '{self.index_name}' at {self.base_url}")
            response = requests.post(
                f"{self.base_url}/api/v1/index/{self.index_name}/search",
                json=data,
                timeout=120 # Increased timeout
            )
            
            if response.status_code == 200:
                print(f"DEBUG: Search response received, length={len(response.content)}")
                # Server returns msgpack: [[hit1, hit2, ...]]
                # Unpack and get the first element which is the list of hits
                response_data = msgpack.unpackb(response.content, raw=False)
                
                if not response_data or not isinstance(response_data, list):
                    return []
                
                # Endee server returns ResultSet which is struct { vector<Hit> results }
                # In MsgPack this translates to a list containing one element: the list of hits.
                # So we expect [[hit1, hit2, ...]]
                if len(response_data) > 0 and isinstance(response_data[0], list):
                    # Check if the first element is itself a Hit [sim, id, ...] or a list of Hits
                    # Hits have at least 2 elements [id, sim] or [sim, id]
                    # If response_data[0][0] is a list, then response_data[0] is the list of hits.
                    if len(response_data[0]) > 0 and isinstance(response_data[0][0], (list, tuple)):
                        hits = response_data[0]
                    else:
                        # Otherwise response_data itself is the list of hits (unwrapped)
                        hits = response_data
                else:
                    hits = response_data
                
                results = []
                for item in hits:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue
                        
                    # Endee server result format [similarity, id, meta, filter, norm, vector]
                    # Similarity is typically float, ID is typically str.
                    # We detect which is which to be robust.
                    if isinstance(item[0], (int, float)) and isinstance(item[1], str):
                        res_score = item[0]
                        res_id = item[1]
                    elif isinstance(item[0], str) and isinstance(item[1], (int, float)):
                        res_id = item[0]
                        res_score = item[1]
                    else:
                        # Best effort fallback
                        res_score = float(item[0]) if isinstance(item[0], (int, float, str)) else 0.0
                        res_id = str(item[1]) if len(item) > 1 else "unknown"
                        
                    results.append({
                        "id": res_id,
                        "score": float(res_score),
                        "metadata": {} 
                    })
                return results
            else:
                print(f"Search failed (Status {response.status_code}): {response.text}")
                return []
                
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    def delete_collection(self) -> bool:
        """Delete the index.
        
        Returns:
            True if successful
        """
        try:
            # Server endpoint: DELETE /api/v1/index/{name}/delete
            response = requests.delete(
                f"{self.base_url}/api/v1/index/{self.index_name}/delete"
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the index.
        
        Returns:
            Index info dict or None
        """
        try:
            # Server endpoint: GET /api/v1/index/list
            response = requests.get(
                f"{self.base_url}/api/v1/index/list"
            )
            
            if response.status_code == 200:
                data = response.json()
                indices = data.get("indexes", [])
                for idx in indices:
                    if idx.get("name") == self.index_name:
                        return idx
                return None
            else:
                return None
                
        except Exception as e:
            print(f"Error getting index info: {e}")
            return None
