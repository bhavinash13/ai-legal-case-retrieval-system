#!/usr/bin/env python3
"""
Enhanced Legal Assistant with improved UX and accuracy
"""
import os, json, time, re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from openai import OpenAI
from pathlib import Path

load_dotenv()

class EnhancedLegalAssistant:
    def __init__(self):
        # Initialize Pinecone and embedding model (always needed)
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(os.getenv("PINECONE_INDEX_NAME", "legal-index-v1"))
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize OpenAI client (may be None if key invalid)
        self.openai_client = None
        self.openai_available = False
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and len(api_key) > 20 and not api_key.startswith("your_"):
                self.openai_client = OpenAI(api_key=api_key)
                # Test the API key with a minimal request
                try:
                    test_response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    self.openai_available = True
                    print("✅ OpenAI API connected successfully")
                except Exception as test_error:
                    print(f"⚠️ OpenAI API key invalid: {test_error}")
                    self.openai_available = False
                    self.openai_client = None
        except Exception as e:
            print(f"⚠️ OpenAI initialization failed: {e}")
            self.openai_available = False
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Load local chunks for fallback
        self.id_to_text = {}
        chunks_path = Path('data/chunks/chunks.jsonl')
        if chunks_path.exists():
            with open(chunks_path, 'r', encoding='utf-8') as f:
                for line in f:
                    j = json.loads(line)
                    self.id_to_text[j['id']] = j.get('text', '')
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        prompt_path = Path('prompts/system_prompt.txt')
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Fallback prompt
            return "You are an AI Legal Assistant for Indian law. Respond naturally and helpfully."
    
    def retrieve_context(self, query: str, top_k: int = 5):
        """Enhanced retrieval with re-ranking"""
        # Primary search
        qvec = self.embed_model.encode([query])[0].tolist()
        results = self.index.query(vector=qvec, top_k=top_k*2, include_metadata=True)
        matches = results.get("matches", [])
        
        # Re-rank by relevance to legal concepts
        legal_keywords = ['section', 'ipc', 'punishment', 'offense', 'crime', 'law', 'act']
        for match in matches:
            text = match.get('metadata', {}).get('text', '').lower()
            keyword_score = sum(1 for kw in legal_keywords if kw in text)
            match['relevance_boost'] = keyword_score * 0.1
            match['adjusted_score'] = match.get('score', 0) + match['relevance_boost']
        
        # Sort by adjusted score and take top_k
        matches = sorted(matches, key=lambda x: x['adjusted_score'], reverse=True)[:top_k]
        return matches
    
    def format_legal_answer(self, query: str, matches: list, mode: str = "openai") -> dict:
        """Generate answer using OpenAI or local mode"""
        
        if mode == "local":
            return self.generate_local_response(query, matches)
        else:
            return self.generate_openai_response(query, matches)
    
    def generate_openai_response(self, query: str, matches: list) -> dict:
        """Generate answer using OpenAI API"""
        
        # Check if OpenAI is available
        if not self.openai_available or not self.openai_client:
            return {"error": "⚠️ OpenAI Mode Error: OpenAI API is not available. Please check your API key or switch to Local Mode."}
        
        # Check if this is a simple greeting
        query_lower = query.lower().strip()
        simple_greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'how are you']
        
        if any(greeting in query_lower for greeting in simple_greetings) and len(query.split()) <= 3:
            user_prompt = f"User Question: {query}"
        else:
            # Build context from legal documents
            context_blocks = []
            for i, match in enumerate(matches, 1):
                metadata = match.get('metadata', {})
                source = metadata.get('source_file', 'Unknown')
                text = metadata.get('text', '')
                context_blocks.append(f"Document {i} ({source}):\n{text}")
            
            context = "\n\n".join(context_blocks) if context_blocks else "No relevant legal documents found."
            user_prompt = f"""Legal Documents:
{context}

User Question: {query}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "answer": answer,
                "sources": [m.get('metadata', {}).get('source_file') for m in matches],
                "confidence": self._assess_confidence(matches),
                "context_used": len(matches),
                "mode": "openai"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"OpenAI API Error: {error_msg}")
            
            if "401" in error_msg or "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                return {"error": "⚠️ OpenAI API Key Error: Your API key is invalid or expired. Switch to Local Mode or update your API key."}
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return {"error": "⚠️ OpenAI Quota Error: No credits available. Switch to Local Mode or add billing."}
            elif "rate_limit" in error_msg.lower():
                return {"error": "⚠️ Rate Limit: Too many requests. Try Local Mode or wait a moment."}
            else:
                return {"error": f"⚠️ OpenAI API Error: {error_msg}"}
    
    def generate_local_response(self, query: str, matches: list) -> dict:
        """Generate answer using only retrieved documents (no OpenAI)"""
        
        if not matches:
            return {
                "answer": "I couldn't find relevant information in the legal database for your query. Please try rephrasing your question or ask about Indian Penal Code (IPC), Criminal Procedure Code (CrPC), or Constitutional law.",
                "sources": [],
                "confidence": "very_low",
                "context_used": 0,
                "mode": "local"
            }
        
        # Build response from top matches
        response_parts = []
        sources = []
        
        response_parts.append(f"📚 Based on the legal documents, here's what I found:\n")
        
        for i, match in enumerate(matches[:3], 1):  # Show top 3 results
            metadata = match.get('metadata', {})
            source = metadata.get('source_file', 'Unknown')
            text = metadata.get('text', '')
            score = match.get('score', 0)
            
            # Clean and truncate text
            text = text.strip()
            if len(text) > 400:
                text = text[:400] + "..."
            
            response_parts.append(f"\n[{i}] From {source} (Relevance: {score:.2f}):\n{text}")
            sources.append(source)
        
        if len(matches) > 3:
            response_parts.append(f"\n\n💡 Found {len(matches)} total matches. Showing top 3 most relevant.")
        
        answer = "\n".join(response_parts)
        
        return {
            "answer": answer,
            "sources": list(set(sources)),
            "confidence": self._assess_confidence(matches),
            "context_used": len(matches),
            "mode": "local"
        }
    

    
    def _assess_confidence(self, matches: list) -> str:
        """Assess confidence based on match quality"""
        if not matches:
            return "very_low"
        
        avg_score = sum(m.get('score', 0) for m in matches) / len(matches)
        
        if avg_score >= 0.8:
            return "high"
        elif avg_score >= 0.6:
            return "medium"
        elif avg_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def display_results(self, query: str, matches: list, answer_data: dict):
        """Enhanced display with better formatting"""
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")
        
        # Show retrieved context
        print(f"\nRETRIEVED CONTEXT ({len(matches)} sources):")
        print("-" * 50)
        for i, match in enumerate(matches, 1):
            metadata = match.get('metadata', {})
            source = metadata.get('source_file', 'Unknown')
            score = match.get('score', 0)
            text_preview = metadata.get('text', '')[:150] + "..."
            
            print(f"[{i}] {source} (Score: {score:.3f})")
            print(f"    {text_preview}")
            print()
        
        # Show answer
        print(f"LEGAL ANALYSIS:")
        print("-" * 50)
        
        if "error" in answer_data:
            print(f"Error: {answer_data['error']}")
        else:
            print(answer_data["answer"])
            
            # Show metadata
            print(f"\nRESPONSE METADATA:")
            print(f"   Confidence: {answer_data.get('confidence', 'unknown').upper()}")
            print(f"   Sources used: {answer_data.get('context_used', 0)}")
            print(f"   Primary sources: {', '.join(set(answer_data.get('sources', [])))}")
        
        print(f"\n{'='*80}")
    
    def interactive_session(self):
        """Enhanced interactive session"""
        print("Enhanced Legal Assistant")
        print("=" * 50)
        print("Ask questions about Indian Penal Code, CrPC, Constitution, etc.")
        print("Type 'exit' to quit, 'help' for examples")
        print()
        
        while True:
            query = input("Legal Query> ").strip()
            
            if query.lower() in ['exit', 'quit']:
                print("Thank you for using Legal Assistant!")
                break
            elif query.lower() == 'help':
                self._show_examples()
                continue
            elif not query:
                continue
            
            try:
                # Retrieve and answer
                matches = self.retrieve_context(query, top_k=5)
                answer_data = self.format_legal_answer(query, matches)
                self.display_results(query, matches, answer_data)
                
            except Exception as e:
                print(f"Error processing query: {e}")
    
    def _show_examples(self):
        """Show example queries"""
        examples = [
            "What is theft under IPC 378?",
            "What is the punishment for murder?",
            "What are fundamental rights?",
            "What is criminal breach of trust?",
            "What is the procedure for arrest?"
        ]
        
        print("\nEXAMPLE QUERIES:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. {example}")
        print()

def main():
    try:
        assistant = EnhancedLegalAssistant()
        assistant.interactive_session()
    except Exception as e:
        print(f"Failed to initialize Legal Assistant: {e}")
        print("Please check your API keys and Pinecone configuration.")

if __name__ == "__main__":
    main()