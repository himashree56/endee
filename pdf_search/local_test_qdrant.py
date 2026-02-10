"""Test script for LocalVectorDB (Qdrant)."""
import os
import shutil
from pathlib import Path
from config import Config

# Force Qdrant mode
os.environ["VECTOR_DB_TYPE"] = "qdrant"
Config.VECTOR_DB_TYPE = "qdrant"

from local_vector_db import LocalVectorDB
import numpy as np

def test_qdrant():
    print("Testing LocalVectorDB (Qdrant)...")
    
    # 1. Initialize
    db = LocalVectorDB()
    print("Initialized DB")
    
    # 2. Create Collection
    success = db.create_collection(dimension=4)
    if not success:
        print("Failed to create collection")
        return
    print("Created Collection")
    
    # 3. Insert Vectors
    vectors = np.array([
        [0.1, 0.2, 0.3, 0.4],
        [0.9, 0.8, 0.7, 0.6]
    ])
    metadata = [
        {"id": "vec1", "text": "Document 1"},
        {"id": "vec2", "text": "Document 2"}
    ]
    
    success = db.insert_vectors(vectors, metadata)
    if not success:
        print("Failed to insert vectors")
        return
    print("Inserted Vectors")
    
    # 4. Search
    print(f"Collection Info: {db.client.get_collection(db.collection_name)}")
    points, _ = db.client.scroll(collection_name=db.collection_name, limit=10)
    print(f"Stored Points: {len(points)}")
    for p in points:
        print(f" - Point ID: {p.id}, Payload: {p.payload}")

    query = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    results = db.search(query, top_k=1)
    
    print(f"Search Results: {results}")
    
    if len(results) > 0 and results[0]['id'] == 'vec1':
        print("SUCCESS: Search returned correct result")
    else:
        print("FAILURE: Search returned wrong result")

    # Cleanup (Optional)
    # shutil.rmtree(Config.PROJECT_ROOT / "qdrant_data", ignore_errors=True)

if __name__ == "__main__":
    test_qdrant()
