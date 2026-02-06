#!/usr/bin/env python3
import os
import json
from pathlib import Path
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

# Config
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not set in environment")

INDEX_NAME = "legal-index-v1"
DIMENSION = 384
METRIC = "cosine"

# Paths
CHUNKS_DIR = Path('data/chunks')
CHUNK_FILE = CHUNKS_DIR / 'chunks.jsonl'

def main():
    print("=== Creating Embeddings and Upserting to Pinecone ===")
    
    # Check chunks file exists
    if not CHUNK_FILE.exists():
        print(f"Error: {CHUNK_FILE} does not exist. Run chunking first!")
        return
    
    # Initialize embedding model
    print("Loading embedding model...")
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    # Initialize Pinecone
    print("Initializing Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Create index if not exists
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    else:
        print(f"Using existing index: {INDEX_NAME}")
    
    index = pc.Index(INDEX_NAME)
    
    # Read chunks
    print("Loading chunks...")
    chunks = []
    with open(CHUNK_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line.strip()))
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Create embeddings and upsert in batches
    batch_size = 50
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    print(f"Processing {total_batches} batches...")
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
        batch = chunks[i:i+batch_size]
        texts = [c['text'] for c in batch]
        
        # Create embeddings
        embeddings = embed_model.encode(texts, show_progress_bar=False)
        
        # Prepare vectors for upsert
        to_upsert = []
        for c, emb in zip(batch, embeddings):
            vector = {
                "id": c['id'],
                "values": emb.tolist(),
                "metadata": {
                    "source_file": c['source_file'],
                    "page": c['page'],
                    "text": c['text'][:8000]  # Limit text size for metadata
                }
            }
            to_upsert.append(vector)
        
        # Upsert to Pinecone
        index.upsert(vectors=to_upsert)
    
    print(f"Successfully upserted {len(chunks)} chunks into Pinecone index '{INDEX_NAME}'")
    print("Next: Run scripts/check_pinecone_index.py to verify")

if __name__ == "__main__":
    main()