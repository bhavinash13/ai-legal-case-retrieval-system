#!/usr/bin/env python3
import os, json, time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from pathlib import Path

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-index-v1")
if not API_KEY:
    raise ValueError("Set PINECONE_API_KEY in .env")

# ------------------------------
# Initialize Pinecone + Embedding model
# ------------------------------
pc = Pinecone(api_key=API_KEY)
index = pc.Index(INDEX_NAME)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# ------------------------------
# Optional: Local snippet lookup
# ------------------------------
CHUNKS_PATH = Path('data/chunks/chunks.jsonl')
id_to_text = {}
if CHUNKS_PATH.exists():
    with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            j = json.loads(line)
            id_to_text[j['id']] = j.get('text', '')

# ------------------------------
# Logging setup
# ------------------------------
LOG_PATH = Path("logs/interactions.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Import generation function
# ------------------------------
from scripts.generate_answer import safe_generate

# ------------------------------
# Query + LLM Answer Function
# ------------------------------
def query_and_answer_once(query: str, top_k: int = 5, model_for_llm: str = "gpt-3.5-turbo"):
    # Generate embedding
    qvec = embed_model.encode([query], convert_to_numpy=True)[0].tolist()
    res = index.query(vector=qvec, top_k=top_k, include_metadata=True)
    matches = res.get("matches", [])

    print(f"\nRetrieved top {len(matches)} matches:")
    for i, m in enumerate(matches, start=1):
        mid = m['id']
        score = m.get('score', 0)
        md = m.get('metadata', {})
        snippet = (id_to_text.get(mid) or md.get('text', ''))[:800].replace('\n', ' ')
        print(f"[{i}] id={mid} | score={score:.4f} | source={md.get('source_file', md.get('source', '-'))}")
        print(snippet)
        print("-" * 60)

    # Call LLM with retrieved context
    llm_out = safe_generate(query, matches, model=model_for_llm)

    # Save interaction log
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    entry = {
        "timestamp": ts,
        "query": query,
        "matches": [
            {"id": m["id"], "score": m.get("score"), "source": m.get("metadata", {}).get("source_file")}
            for m in matches
        ],
        "llm_response": llm_out,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Print formatted output
    print("\n=== 🧠 LLM Legal Answer ===")
    if isinstance(llm_out, dict) and "answer" in llm_out:
        print("Answer:\n", llm_out["answer"])
        if llm_out.get("citations"):
            print("\nCitations:")
            for c in llm_out["citations"]:
                print(" -", c)
        if llm_out.get("confidence"):
            print("\nConfidence:", llm_out["confidence"])
    else:
        print(llm_out)
    print("============================")
    return entry

# ------------------------------
# Interactive loop
# ------------------------------
def interactive_loop():
    print("⚖️  Legal AI Assistant — Interactive Query Mode")
    print("Type 'exit' to quit.\n")
    while True:
        q = input("Query> ").strip()
        if q.lower() in ("exit", "quit"):
            break
        try:
            query_and_answer_once(q)
        except Exception as e:
            print("❌ Error:", e)

if __name__ == "__main__":
    interactive_loop()
