# scripts/llm_util.py
import textwrap
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT_PATH = Path("prompts/system_prompt.txt")
SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8") if SYSTEM_PROMPT_PATH.exists() else ""

def build_context_prompt(query: str, matches: list, max_chars: int = 4000) -> str:
    """
    Assemble system prompt + query + limited evidence blocks.
    matches: list of dicts from Pinecone with 'id', 'score', 'metadata' keys.
    """
    evidence_blocks = []
    cur = 0
    for i, m in enumerate(matches, start=1):
        md = m.get("metadata", {})
        excerpt = md.get("text", "").replace("\n", " ").strip()[:350]
        doc = md.get("source_file", md.get("source","unknown"))
        chunk_id = m.get("id", "<id>")
        block = f"[{i}] {doc} | id={chunk_id}\nExcerpt: {excerpt}\nScore: {m.get('score', 0):.4f}\n"
        if cur + len(block) > max_chars:
            break
        evidence_blocks.append(block)
        cur += len(block)

    evidence_text = "\n\n".join(evidence_blocks) if evidence_blocks else "No evidence blocks available."
    prompt = textwrap.dedent(f"""
    {SYSTEM_PROMPT}

    Query: {query}

    Evidence:
    {evidence_text}

    Instructions:
    - Answer concisely and produce JSON only as specified in the system prompt.
    """).strip()

    return prompt
