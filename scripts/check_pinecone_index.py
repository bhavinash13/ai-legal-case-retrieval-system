#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
idx = pc.Index("legal-index-v1")
stats = idx.describe_index_stats()
print(stats)
total = stats.get("total_vector_count", 0)
print("Total vectors:", total)

