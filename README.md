# AI-Based Legal Reference and Case Retrieval System

A complete pipeline for processing legal documents, creating embeddings, and enabling semantic search using OpenAI embeddings and Pinecone vector database.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
3. **Pinecone API Key** - Get from [Pinecone Console](https://app.pinecone.io/)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy `.env` file and add your API keys:
   ```bash
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=us-east-1
   PINECONE_INDEX_NAME=legal-index-v1
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Add PDF documents:**
   - Place your legal PDF files in `data/raw/` directory
   - The system will process any `.pdf` files found there

## 📋 Pipeline Execution

Run the scripts in this exact order:

### Step 1: Preprocess Data
```bash
python 01_preprocess_data.py
```
**What it does:**
- Extracts text from PDFs in `data/raw/`
- Removes headers/footers automatically
- Normalizes text (fixes hyphenation, whitespace)
- Saves processed data to `data/extracted/`
- Creates manifest with file tracking

**Expected output:**
- Processed files in `data/extracted/*.json`
- Manifest file in `manifests/manifest.jsonl`

### Step 2: Create Embeddings
```bash
python 02_create_embeddings.py
```
**What it does:**
- Creates token-aware chunks (500-800 tokens each, 100 token overlap)
- Generates OpenAI embeddings using `text-embedding-3-small`
- Saves chunks and embeddings with metadata
- Optimizes for semantic retrieval accuracy

**Expected output:**
- Chunks file: `data/chunks/chunks.jsonl`
- Embeddings file: `data/embeddings/embeddings.jsonl`

### Step 3: Upload to Pinecone
```bash
python 03_upsert_pinecone.py
```
**What it does:**
- Creates Pinecone index (if doesn't exist)
- Uploads embeddings with rich metadata
- Includes source file, page numbers, titles, dates
- Verifies successful upload

**Expected output:**
- Vectors uploaded to Pinecone index
- Confirmation of successful upload

### Step 4: Test Retrieval
```bash
python 04_test_retrieval.py
```
**What it does:**
- Tests with sample legal queries
- Evaluates retrieval quality and relevance
- Provides interactive query mode
- Shows detailed results with scores

**Expected output:**
- Retrieval test results
- Quality evaluation metrics
- Interactive query interface

## 🎯 Key Features

### Advanced Text Processing
- **Smart PDF extraction** with pdfplumber
- **Automatic header/footer removal** 
- **Legal document normalization** (hyphenation, citations)
- **Token-aware chunking** for optimal embedding quality

### High-Quality Embeddings
- **OpenAI text-embedding-3-small** (1536 dimensions)
- **Token-optimized chunks** (500-800 tokens)
- **Semantic overlap** (100 tokens) for context preservation
- **Rich metadata** (source, page, title, date)

### Optimized Retrieval
- **Cosine similarity** search in Pinecone
- **Metadata filtering** capabilities
- **Relevance scoring** and evaluation
- **Interactive testing** interface

## 📊 Sample Queries

The system is optimized for legal queries like:
- "What is the doctrine of res judicata?"
- "How does contract formation work in common law?"
- "What are the elements of negligence in tort law?"
- "Explain the concept of judicial review"
- "What constitutes breach of fiduciary duty?"

## 🔧 Configuration Options

### Chunking Parameters (in `02_create_embeddings.py`)
```python
TARGET_CHUNK_TOKENS = 600  # Target tokens per chunk
MAX_CHUNK_TOKENS = 800     # Maximum tokens per chunk  
OVERLAP_TOKENS = 100       # Overlap between chunks
MIN_CHUNK_TOKENS = 50      # Minimum viable chunk size
```

### Embedding Model Options
- `text-embedding-3-small` (1536 dim) - Cost-effective, good quality
- `text-embedding-3-large` (3072 dim) - Higher quality, more expensive

### Pinecone Configuration
- **Metric:** Cosine similarity (best for semantic search)
- **Cloud:** AWS (configurable)
- **Region:** us-east-1 (configurable)

## 📁 Directory Structure

```
ai-legal-reference/
├── data/
│   ├── raw/              # Place PDF files here
│   ├── extracted/        # Processed text files
│   ├── chunks/          # Text chunks
│   └── embeddings/      # Generated embeddings
├── manifests/           # File tracking
├── 01_preprocess_data.py    # PDF extraction & normalization
├── 02_create_embeddings.py  # Chunking & embedding generation
├── 03_upsert_pinecone.py   # Vector database upload
├── 04_test_retrieval.py    # Retrieval testing
├── requirements.txt     # Dependencies
├── .env                # Environment variables
└── README.md           # This file
```

## 🚨 Troubleshooting

### Common Issues

1. **"No PDF files found"**
   - Ensure PDF files are in `data/raw/` directory
   - Check file permissions

2. **"OPENAI_API_KEY not set"**
   - Add your OpenAI API key to `.env` file
   - Ensure `.env` is in project root

3. **"PINECONE_API_KEY not set"**
   - Add your Pinecone API key to `.env` file
   - Verify API key is valid

4. **"No vectors in index"**
   - Run scripts in order: 01 → 02 → 03 → 04
   - Check for errors in previous steps

5. **Poor retrieval quality**
   - Add more diverse legal documents
   - Adjust chunking parameters
   - Try `text-embedding-3-large` model

### Performance Tips

- **Batch processing:** Scripts handle large document sets efficiently
- **Memory usage:** Embeddings are processed in batches
- **API limits:** Built-in rate limiting for OpenAI API
- **Error handling:** Robust error handling with detailed logging

## 💡 Next Steps

After successful retrieval testing, you can:

1. **Add more documents** to improve coverage
2. **Fine-tune chunking** parameters for your specific documents
3. **Implement filtering** by document type, date, or jurisdiction
4. **Add LLM integration** for answer generation
5. **Build a web interface** (Streamlit, FastAPI, etc.)
6. **Add evaluation metrics** for retrieval quality

## 📈 Monitoring & Evaluation

The system includes built-in evaluation:
- **Relevance scoring** based on similarity scores
- **Quality assessment** (Excellent/Good/Fair/Poor)
- **Batch evaluation** for systematic testing
- **Interactive testing** for manual verification

## 🔒 Security Notes

- Keep API keys secure in `.env` file
- Don't commit `.env` to version control
- Use environment-specific configurations
- Monitor API usage and costs

---

**Ready to process your legal documents!** 🏛️⚖️

Run the pipeline step by step and enjoy high-quality semantic search over your legal document collection.