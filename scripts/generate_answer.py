# scripts/generate_answer.py
import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def safe_generate(query, matches, model="gpt-3.5-turbo"):
    """
    Generate a natural legal answer using the retrieved matches.
    """
    try:
        # Combine retrieved context from Pinecone
        context_blocks = []
        for m in matches:
            md = m.get("metadata", {})
            src = md.get("source_file", md.get("source", ""))
            txt = md.get("text", "")
            context_blocks.append(f"Source: {src}\n{txt}")
        context = "\n\n".join(context_blocks) if context_blocks else "No relevant evidence found."

        # Construct the natural prompt
        prompt = f"""
You are a helpful AI assistant. Answer like a human in normal conversation.

IMPORTANT: 
- Give ONLY 3-4 simple sentences
- NO headings, NO bullet points, NO structured format
- NEVER write "Definition:", "Punishment:", "Example:" or any labels
- Just answer the question naturally and directly

Context from legal documents:
{context}

Question: {query}

Answer naturally in 3-4 sentences maximum:
"""

        # Generate the answer using the OpenAI Chat API
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer questions naturally in 3-4 sentences without any structured format or headings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        answer_text = completion.choices[0].message.content.strip()

        # Return structured response
        return {
            "answer": answer_text,
            "citations": [m.get("metadata", {}).get("source_file") for m in matches if m.get("metadata")],
            "confidence": "high" if len(matches) > 2 else "medium"
        }

    except Exception as e:
        return {"error": f"LLM call failed: {e}"}