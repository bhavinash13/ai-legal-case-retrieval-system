#!/usr/bin/env python3
"""
System Diagnostic Tool for AI Legal Reference System
Run this to check if everything is configured correctly
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_status(check_name, status, message=""):
    symbol = "✅" if status else "❌"
    print(f"{symbol} {check_name}")
    if message:
        print(f"   → {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 8
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print_status(
        "Python Version", 
        is_valid, 
        f"Version {version_str} {'(OK)' if is_valid else '(Need 3.8+)'}"
    )
    return is_valid

def check_packages():
    """Check if required packages are installed"""
    print_header("CHECKING PYTHON PACKAGES")
    
    packages = {
        'streamlit': 'streamlit',
        'openai': 'openai',
        'pinecone': 'pinecone',
        'sentence_transformers': 'sentence-transformers',
        'pymongo': 'pymongo',
        'bcrypt': 'bcrypt',
        'dotenv': 'python-dotenv',
        'pdfplumber': 'pdfplumber'
    }
    
    all_installed = True
    missing = []
    
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
            print_status(package_name, True, "Installed")
        except ImportError:
            print_status(package_name, False, "NOT INSTALLED")
            missing.append(package_name)
            all_installed = False
    
    if missing:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
    
    return all_installed

def check_env_file():
    """Check .env file configuration"""
    print_header("CHECKING ENVIRONMENT CONFIGURATION")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print_status(".env file", False, "File not found")
        return False
    
    print_status(".env file", True, "File exists")
    
    # Read and check variables
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_status("Read .env", False, f"Error: {e}")
        return False
    
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'PINECONE_API_KEY': 'Pinecone API Key',
        'MONGO_URI': 'MongoDB Connection URI'
    }
    
    all_valid = True
    
    for var, description in required_vars.items():
        if f"{var}=" in content:
            # Extract value
            for line in content.split('\n'):
                if line.startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if value and 'your_' not in value.lower():
                        print_status(description, True, "Configured")
                    else:
                        print_status(description, False, "Empty or placeholder")
                        all_valid = False
                    break
        else:
            print_status(description, False, "Not found in .env")
            all_valid = False
    
    return all_valid

def check_mongodb_connection():
    """Test MongoDB connection"""
    print_header("CHECKING MONGODB CONNECTION")
    
    try:
        from db_connection import get_collections
        collections = get_collections()
        
        if collections['available']:
            print_status("MongoDB Connection", True, "Connected successfully")
            print_status("Users Collection", collections['users'] is not None)
            print_status("Chats Collection", collections['chats'] is not None)
            print_status("bcrypt Library", collections['bcrypt'] is not None)
            return True
        else:
            print_status("MongoDB Connection", False, "Dependencies missing")
            return False
            
    except Exception as e:
        print_status("MongoDB Connection", False, f"Error: {e}")
        return False

def check_pinecone_connection():
    """Test Pinecone connection"""
    print_header("CHECKING PINECONE CONNECTION")
    
    try:
        from dotenv import load_dotenv
        from pinecone import Pinecone
        
        load_dotenv()
        
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "legal-index-v1")
        
        if not api_key:
            print_status("Pinecone API Key", False, "Not found in .env")
            return False
        
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        vector_count = stats.get('total_vector_count', 0)
        
        print_status("Pinecone Connection", True, "Connected successfully")
        print_status("Index Name", True, index_name)
        print_status("Vector Count", vector_count > 0, f"{vector_count} vectors")
        
        return vector_count > 0
        
    except Exception as e:
        print_status("Pinecone Connection", False, f"Error: {e}")
        return False

def check_openai_connection():
    """Test OpenAI connection"""
    print_header("CHECKING OPENAI CONNECTION")
    
    try:
        from dotenv import load_dotenv
        from openai import OpenAI
        
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print_status("OpenAI API Key", False, "Not found in .env")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        
        print_status("OpenAI Connection", True, "API key valid")
        print_status("Model Access", True, "gpt-3.5-turbo accessible")
        
        return True
        
    except Exception as e:
        print_status("OpenAI Connection", False, f"Error: {e}")
        return False

def check_data_files():
    """Check if data files exist"""
    print_header("CHECKING DATA FILES")
    
    paths = {
        'data/raw': 'PDF files directory',
        'data/extracted': 'Extracted text directory',
        'data/chunks/chunks.jsonl': 'Text chunks file',
        'prompts/system_prompt.txt': 'System prompt file'
    }
    
    all_exist = True
    
    for path, description in paths.items():
        path_obj = Path(path)
        exists = path_obj.exists()
        
        if path_obj.is_dir():
            if exists:
                file_count = len(list(path_obj.glob('*')))
                print_status(description, exists, f"{file_count} files")
            else:
                print_status(description, False, "Directory not found")
                all_exist = False
        else:
            print_status(description, exists, "Found" if exists else "Not found")
            if not exists:
                all_exist = False
    
    return all_exist

def check_app_files():
    """Check if main application files exist"""
    print_header("CHECKING APPLICATION FILES")
    
    files = {
        'app.py': 'Main Streamlit app',
        'launcher.py': 'App launcher',
        'auth_backend.py': 'Authentication module',
        'chat_manager.py': 'Chat management module',
        'db_connection.py': 'Database connection module',
        'scripts/enhanced_legal_assistant_QA.py': 'Legal assistant module'
    }
    
    all_exist = True
    
    for file, description in files.items():
        exists = Path(file).exists()
        print_status(description, exists, "Found" if exists else "NOT FOUND")
        if not exists:
            all_exist = False
    
    return all_exist

def main():
    """Run all diagnostic checks"""
    print("\n" + "🔍 AI LEGAL REFERENCE SYSTEM - DIAGNOSTIC TOOL".center(60))
    print("="*60)
    
    results = {}
    
    # Run all checks
    print_header("SYSTEM REQUIREMENTS")
    results['python'] = check_python_version()
    
    results['packages'] = check_packages()
    results['env'] = check_env_file()
    results['app_files'] = check_app_files()
    results['data_files'] = check_data_files()
    
    # Connection checks (only if basics are OK)
    if results['packages'] and results['env']:
        results['mongodb'] = check_mongodb_connection()
        results['pinecone'] = check_pinecone_connection()
        results['openai'] = check_openai_connection()
    else:
        print("\n⚠️  Skipping connection checks (fix basic requirements first)")
        results['mongodb'] = False
        results['pinecone'] = False
        results['openai'] = False
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"\n📊 Passed: {passed_checks}/{total_checks} checks")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL CHECKS PASSED!")
        print("✅ Your system is ready to run the AI Legal Assistant")
        print("\n🚀 Start the app with:")
        print("   python launcher.py")
        print("   OR")
        print("   streamlit run app.py")
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("❌ Please fix the issues above before running the app")
        
        # Provide specific guidance
        if not results['packages']:
            print("\n💡 Install missing packages:")
            print("   pip install -r requirements.txt")
        
        if not results['env']:
            print("\n💡 Configure your .env file:")
            print("   Copy .env.example to .env and add your API keys")
        
        if not results['mongodb']:
            print("\n💡 Check MongoDB connection:")
            print("   Verify MONGO_URI in .env file")
            print("   Ensure MongoDB Atlas cluster is running")
        
        if not results['pinecone']:
            print("\n💡 Check Pinecone setup:")
            print("   Verify PINECONE_API_KEY in .env file")
            print("   Run: python 03_upsert_pinecone.py")
        
        if not results['openai']:
            print("\n💡 Check OpenAI setup:")
            print("   Verify OPENAI_API_KEY in .env file")
            print("   Check API key at: https://platform.openai.com/api-keys")
    
    print("\n" + "="*60)
    
    return passed_checks == total_checks

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Diagnostic interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        sys.exit(1)
