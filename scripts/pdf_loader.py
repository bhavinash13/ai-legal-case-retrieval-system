# scripts/pdf_loader.py
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pdfplumber
import re

RAW_DIR = Path("data/raw")
EXTRACT_DIR = Path("data/extracted")
MANIFEST = Path("manifests/manifest.jsonl")
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_text_pdfplumber(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            pages.append(text)
    return pages

def simple_metadata_from_first_page(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else ""
    date_re = re.search(r"(\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}\b)|(\b\d{4}-\d{2}-\d{2}\b)", text, re.I)
    date = date_re.group(0) if date_re else ""
    return {"title": title, "date": date}

def save_extracted(pdf_path, pages, metadata):
    fname = Path(pdf_path).stem
    out_path = EXTRACT_DIR / f"{fname}.pages.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"pages": pages, "metadata": metadata}, f, ensure_ascii=False, indent=2)
    return out_path

def process_one(pdf_path):
    pages = extract_text_pdfplumber(pdf_path)
    meta = simple_metadata_from_first_page(pages[0] if pages else "")
    manifest_entry = {
        "source_path": str(pdf_path),
        "sha256": sha256_file(pdf_path),
        "num_pages": len(pages),
        "extracted_path": None,
        "metadata": meta,
        "extraction_status": "ok" if pages else "empty",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    out = save_extracted(pdf_path, pages, meta)
    manifest_entry["extracted_path"] = str(out)
    with open(MANIFEST, "a", encoding="utf-8") as mf:
        mf.write(json.dumps(manifest_entry) + "\n")
    return manifest_entry

if __name__ == "__main__":
    pdfs = list(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in", RAW_DIR)
    for p in pdfs:
        print("Processing:", p.name)
        info = process_one(p)
        print("Saved extracted:", info["extracted_path"], "| pages:", info["num_pages"])
