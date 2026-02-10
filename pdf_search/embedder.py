"""Text embedding generation using fastembed (lightweight)."""
import numpy as np
from typing import List, Union
from fastembed import TextEmbedding
from config import Config


class Embedder:
    """Generate embeddings for text using fastembed (ONNX Runtime)."""
    
    def __init__(self, model_name: str = None):
        """Initialize embedder.
        
        Args:
            model_name: Name of embedding model (default: BAAI/bge-small-en-v1.5 or similar supported by fastembed)
        """
        # FastEmbed uses slightly different naming, but supports "BAAI/bge-small-en-v1.5" which is better/lighter than MiniLM
        # Or we can stick to a MiniLM equivalent if supported.
        # "fast-bge-small-en" or "BAAI/bge-small-en-v1.5" are solid choices.
        # Let's use a standard supported lightweight one.
        self.model_name = "BAAI/bge-small-en-v1.5" # Hardcoded efficient model for Free Tier
        
        # Setting a local cache directory for persistence and Docker build integration
        self.cache_dir = Config.PROJECT_ROOT / "model_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        print(f"Loading embedding model: {self.model_name}")
        self.model = TextEmbedding(
            model_name=self.model_name,
            cache_dir=str(self.cache_dir)
        )
        print(f"Model loaded.")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        # FastEmbed returns a generator of embeddings
        embeddings = list(self.model.embed([text]))
        return embeddings[0]
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        # FastEmbed handles batching internally, but we can pass list
        embeddings = list(self.model.embed(texts, batch_size=batch_size))
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        # BGE-Small is 384
        return 384
