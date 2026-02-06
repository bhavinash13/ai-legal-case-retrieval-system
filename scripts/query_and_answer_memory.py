# scripts/query_and_answer_memory.py
import os, json, time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from pathlib import Path
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone + embedding model
API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-index-v1")

pc = Pinecone(api_key=API_KEY)
index = pc.Index(INDEX_NAME)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# Memory store
conversation_history = []

def get_context_from_history() -> str:
    """Concatenate prior Q&A pairs for continuity."""
    return "\n\n".join(
        [f"Q: {h['query']}\nA: {h['answer']}" for h in conversation_history[-3:]]  # last 3 turns
    )

def query_and_answer_with_memory(query: str, top_k: int = 5):
    qvec = embed_model.encode([query], convert_to_numpy=True)[0].tolist()
    res = index.query(vector=qvec, top_k=top_k, include_metadata=True)
    matches = res.get("matches", [])

    # Context from previous turns
    history_text = get_context_from_history()
    context_blocks = "\n\n".join(
        [m.get("metadata", {}).get("text", "") for m in matches]
    )

    # Load system prompt
    system_prompt_path = Path('prompts/system_prompt.txt')
    if system_prompt_path.exists():
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    else:
        system_prompt = "You are an AI Legal Assistant for Indian law. Respond naturally and helpfully."
    
    prompt = f"""
Conversation history:
{history_text}

Legal Documents:
{context_blocks}

User Question: {query}
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        answer = completion.choices[0].message.content.strip()
        conversation_history.append({"query": query, "answer": answer})
        print("\n=== 🧠 LLM Legal Answer ===")
        print(answer)
        print("============================")
    except Exception as e:
        print("Error during LLM call:", e)

if __name__ == "__main__":
    print("Conversational Legal Assistant. Type 'exit' to quit.")
    while True:
        q = input("\nQuery> ").strip()
        if q.lower() in ("exit", "quit"):
            break
        query_and_answer_with_memory(q)
