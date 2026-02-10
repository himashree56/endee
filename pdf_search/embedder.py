"""Text embedding generation using fastembed (memory efficient)."""
import numpy as np
from typing import List, Union
from fastembed import TextEmbedding
from config import Config


class Embedder:
    """Generate embeddings for text using fastembed for low memory usage."""
    
    def __init__(self, model_name: str = None):
        """Initialize embedder.
        
        Args:
            model_name: Name of fastembed model
        """
        # Default to BAAI/bge-small-en-v1.5 if not specified
        self.model_name = model_name or Config.EMBEDDING_MODEL
        print(f"Loading embedding model: {self.model_name}")
        self.model = TextEmbedding(model_name=self.model_name)
        print(f"Model loaded.")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        # fastembed returns an iterator, we need the first result
        embeddings = list(self.model.embed([text]))
        return np.array(embeddings[0])
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar (ignored by fastembed as it is fast)
            
        Returns:
            Array of embeddings (N x D)
        """
        embeddings = list(self.model.embed(texts, batch_size=batch_size))
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Embedding dimension
        """
        # For BAAI/bge-small-en-v1.5 and all-MiniLM-L6-v2, it's 384
        # We can detect it from a sample if needed, but usually it's in Config
        return Config.EMBEDDING_DIM
