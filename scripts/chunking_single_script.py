#!/usr/bin/env python3
"""
Robust chunking script: reads data/extracted/*.json and produces data/chunks/chunks.jsonl.

Handles a variety of input shapes: dict with "pages" list (where page items may be dicts or strings),
top-level list of dicts/strings, single dict with "text", or arbitrary JSON (stringified).
"""
import os, json, glob, re
from pathlib import Path
from tqdm import tqdm

ROOT = Path('.')
IN_DIR = ROOT / 'data' / 'extracted'
OUT_DIR = ROOT / 'data' / 'chunks'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / 'chunks.jsonl'

MAX_WORDS = 250   # target chunk words
OVERLAP = 100      # overlap words
MIN_WORDS = 40    # drop tiny chunks

def simple_sentences(text):
    text = text.replace('\r', ' ').strip()
    # split on sentence enders and some punctuation commonly used in legal docs
    sents = re.split(r'(?<=[\.\?\!;:\n])\s+', text)
    return [s.strip() for s in sents if s.strip()]

def chunk_text(text, max_words=MAX_WORDS, overlap=OVERLAP):
    sents = simple_sentences(text)
    chunks = []
    cur = []
    cur_words = 0
    for sent in sents:
        ws = len(sent.split())
        if cur and cur_words + ws > max_words:
            chunks.append(' '.join(cur).strip())
            # keep overlap
            if overlap > 0:
                last_words = ' '.join(' '.join(cur).split()[-overlap:])
                cur = [last_words]
                cur_words = len(last_words.split())
            else:
                cur = []
                cur_words = 0
        cur.append(sent)
        cur_words += ws
    if cur:
        chunks.append(' '.join(cur).strip())
    # filter tiny chunks
    return [c for c in chunks if len(c.split()) >= MIN_WORDS]

def read_pages_json(path):
    """
    Return list of {'page': <maybe>, 'text': <str>} entries for a given file.
    Works with:
      - {"pages": [ {"page":1,"text":"..."}, {"page":2,"text":"..."} ]}
      - {"pages": ["text1", "text2", ...]}
      - [{"page":1, "text":"..."}, "some text", ...]
      - {"text": "..."} single doc
      - anything else -> stringified
    """
    with open(path, 'r', encoding='utf-8') as f:
        try:
            j = json.load(f)
        except Exception as e:
            # corrupted JSON? return raw file contents as single entry
            print(f"Warning: failed to parse JSON in {path} ({e}). Using raw text fallback.")
            raw = Path(path).read_text(encoding='utf-8', errors='ignore')
            return [{'page': None, 'text': raw}]

    entries = []
    # Case 1: dict with "pages"
    if isinstance(j, dict) and 'pages' in j and isinstance(j['pages'], list):
        for idx, p in enumerate(j['pages']):
            # page item might be dict, string, or something else
            if isinstance(p, dict):
                text = p.get('text') or p.get('content') or ''
                page_no = p.get('page') or p.get('page_no') or None
                entries.append({'page': page_no, 'text': text})
            elif isinstance(p, str):
                entries.append({'page': idx, 'text': p})
            else:
                # unknown type, stringify
                entries.append({'page': idx, 'text': json.dumps(p)})
    # Case 2: top-level list
    elif isinstance(j, list):
        for idx, item in enumerate(j):
            if isinstance(item, dict):
                text = item.get('text') or item.get('content') or ''
                page_no = item.get('page') or None
                entries.append({'page': page_no, 'text': text})
            elif isinstance(item, str):
                entries.append({'page': idx, 'text': item})
            else:
                entries.append({'page': idx, 'text': json.dumps(item)})
    # Case 3: dict with 'text'
    elif isinstance(j, dict) and 'text' in j:
        entries.append({'page': j.get('page'), 'text': j.get('text')})
    else:
        # fallback: stringify the whole JSON
        entries.append({'page': None, 'text': json.dumps(j)})
    return entries

all_files = sorted(glob.glob(str(IN_DIR / '*.json')) + glob.glob(str(IN_DIR / '*.jsonl')))
if not all_files:
    print("No files found in", IN_DIR)
    raise SystemExit(1)

with open(OUT_PATH, 'w', encoding='utf-8') as fout:
    for fp in tqdm(all_files, desc='Files'):
        entries = read_pages_json(fp)
        base = Path(fp).stem
        for e_idx, e in enumerate(entries):
            text = (e.get('text') or '').strip()
            if not text or len(text.split()) < 50:
                # skip empty or extremely short items
                continue
            chunks = chunk_text(text)
            for ci, c in enumerate(chunks):
                obj = {
                    "id": f"{base}-{e_idx}-{ci}",
                    "source_file": Path(fp).name,
                    "page": e.get('page'),
                    "text": c
                }
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

print("Wrote chunks to", OUT_PATH)
