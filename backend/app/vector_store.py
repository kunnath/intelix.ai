import os
import time
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the embedding model with increased timeout and retry logic
MAX_RETRIES = 3
model = None

for attempt in range(MAX_RETRIES):
    try:
        logger.info(f"Attempting to load model (attempt {attempt + 1}/{MAX_RETRIES})...")
        # Increase the timeout for model download
        os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '120'  # 120 seconds timeout
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully!")
        break
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        if attempt < MAX_RETRIES - 1:
            wait_time = (attempt + 1) * 5  # Exponential backoff
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            logger.error("Failed to load model after multiple attempts")
            # Initialize with a fallback or raise an exception as needed
            raise

class VectorStore:
    def __init__(self):
        # Connect to Qdrant
        # In local development, connect to localhost
        # In Docker, connect to the service name
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.client = QdrantClient(url=qdrant_host, port=6333)
        self.collection_name = "test_cases"
        self._create_collection_if_not_exists()
    
    def model_is_loaded(self):
        """Check if the sentence transformer model is loaded."""
        return model is not None
        
    def _create_collection_if_not_exists(self):
        """Create a collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text."""
        return model.encode(text).tolist()
    
    def store_test_case(self, jira_id: str, description: str, test_cases: List[Dict[str, Any]]) -> str:
        """Store test case with JIRA ID as payload."""
        # Combine description and test case for embedding
        embedding_text = f"{description} {json.dumps(test_cases)}"
        embedding = self._generate_embedding(embedding_text)
        
        # Create a unique ID from JIRA ID
        point_id = hash(jira_id) % (2**63)
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "jira_id": jira_id,
                        "description": description,
                        "test_cases": test_cases
                    }
                )
            ]
        )
        
        return jira_id
    
    def retrieve_test_case(self, jira_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve test case by JIRA ID."""
        # Search for the test case with the given JIRA ID
        point_id = hash(jira_id) % (2**63)
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if points and len(points) > 0:
                return points[0].payload
            return None
        except Exception as e:
            print(f"Error retrieving test case: {e}")
            return None
    
    def search_similar_test_cases(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar test cases using semantic search."""
        query_embedding = self._generate_embedding(query)
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        results = []
        for point in search_result:
            results.append(point.payload)
        
        return results
