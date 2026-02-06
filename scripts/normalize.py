# scripts/normalize.py
import json
from pathlib import Path
import re
from collections import Counter

EXTRACT_DIR = Path("data/extracted")
MANIFEST = Path("manifests/manifest.jsonl")

def detect_repeating_header_footer(pages, look_lines=2, threshold=0.8):
    heads, foots = [], []
    for p in pages:
        lines = [l for l in (p or "").splitlines()]
        head = "\n".join(lines[:look_lines]).strip()
        foot = "\n".join(lines[-look_lines:]).strip() if lines else ""
        heads.append(head)
        foots.append(foot)
    n = max(1, len(pages))
    head_counts = Counter(h for h in heads if h)
    foot_counts = Counter(f for f in foots if f)
    head_candidates = [h for h, c in head_counts.items() if c / n >= threshold]
    foot_candidates = [f for f, c in foot_counts.items() if c / n >= threshold]
    return head_candidates, foot_candidates

def remove_candidates_from_page(text, candidates):
    for c in candidates:
        if c and c in text:
            text = text.replace(c, "")
    return text

def fix_hyphenation(text):
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def normalize_file(path):
    j = json.load(open(path, "r", encoding="utf-8"))
    pages = j.get("pages", [])
    head_cand, foot_cand = detect_repeating_header_footer(pages)
    normalized = []
    for p in pages:
        t = remove_candidates_from_page(p, head_cand)
        t = remove_candidates_from_page(t, foot_cand)
        t = fix_hyphenation(t)
        normalized.append(t)
    j["pages_normalized"] = normalized
    with open(path, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    return path.name, len(normalized)

if __name__ == "__main__":
    files = list(EXTRACT_DIR.glob("*.pages.json"))
    if not files:
        print("No extracted JSON files found in", EXTRACT_DIR)
    for f in files:
        name, count = normalize_file(f)
        print("Normalized:", name, "| pages:", count)
