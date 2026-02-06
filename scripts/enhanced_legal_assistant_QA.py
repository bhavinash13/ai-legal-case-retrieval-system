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
        # Initialize clients
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(os.getenv("PINECONE_INDEX_NAME", "legal-index-v1"))
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        
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
    
    def format_legal_answer(self, query: str, matches: list) -> dict:
        """Generate answer using system prompt"""
        
        # Check if this is a simple greeting or non-legal query
        query_lower = query.lower().strip()
        simple_greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'how are you']
        
        # For simple greetings, don't use legal documents
        if any(greeting in query_lower for greeting in simple_greetings) and len(query.split()) <= 3:
            user_prompt = f"User Question: {query}"
        else:
            # Build context from legal documents for legal queries
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
                temperature=0.1,
                max_tokens=100
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "answer": answer,
                "sources": [m.get('metadata', {}).get('source_file') for m in matches],
                "confidence": self._assess_confidence(matches),
                "context_used": len(matches)
            }
            
        except Exception as e:
            return {"error": f"Failed to generate answer: {e}"}
    

    
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