#!/usr/bin/env python3
import os, json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from pathlib import Path

load_dotenv()
API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-index-v1")

pc = Pinecone(api_key=API_KEY)
index = pc.Index(INDEX_NAME)
model = SentenceTransformer('all-MiniLM-L6-v2')

CHUNKS_PATH = Path('data/chunks/chunks.jsonl')
id_to_text = {}
with open(CHUNKS_PATH,'r',encoding='utf-8') as f:
    for line in f:
        j = json.loads(line)
        id_to_text[j['id']] = j['text']

def query(q, top_k=5):
    vec = model.encode([q], convert_to_numpy=True)[0].tolist()
    res = index.query(vector=vec, top_k=top_k, include_metadata=True)
    return res

print("Interactive query. Type 'exit' to quit.")
while True:
    q = input("\nQuery> ").strip()
    if q.lower() in ('exit','quit'):
        break
    res = query(q, top_k=5)
    matches = res.get('matches', [])
    for i, m in enumerate(matches, start=1):
        mid = m['id']
        score = m.get('score',0)
        md = m.get('metadata', {})
        snippet = id_to_text.get(mid, '')[:800].replace('\n',' ')
        print(f"\nRank {i} | id={mid} | score={score:.4f} | source={md.get('source_file')}")
        print(snippet)
        print("-"*60)
