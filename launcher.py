#!/usr/bin/env python3
"""
⚖️ AI Legal Reference System Launcher
Easy startup script for the legal AI assistant
"""
import subprocess
import sys
import os
from pathlib import Path
import importlib.util

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = {
        'streamlit': 'streamlit',
        'openai': 'openai', 
        'pinecone': 'pinecone-client',
        'sentence_transformers': 'sentence-transformers',
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            if import_name == 'pinecone':
                # Special check for pinecone
                spec = importlib.util.find_spec('pinecone')
                if spec is None:
                    missing_packages.append(package_name)
            else:
                __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print("\n💡 Or install all requirements:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists with required variables"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("\n📝 Create a .env file with:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        print("   PINECONE_API_KEY=your_pinecone_api_key_here")
        print("   PINECONE_INDEX_NAME=legal-index-v1")
        print("   PINECONE_ENVIRONMENT=us-east-1")
        return False
    
    # Check if required variables exist
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY']
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        if f"{var}=" not in content:
            missing_vars.append(var)
        elif f"{var}=" in content:
            # Check if variable has a value
            lines = content.split('\n')
            for line in lines:
                if line.startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if not value or value == 'your_openai_api_key_here' or value == 'your_pinecone_api_key_here':
                        empty_vars.append(var)
                    break
    
    if missing_vars:
        print("❌ Missing environment variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    if empty_vars:
        print("❌ Empty environment variables in .env:")
        for var in empty_vars:
            print(f"   - {var} (please add your actual API key)")
        return False
    
    return True

def check_data_structure():
    """Check if required data directories exist"""
    required_dirs = [
        'data',
        'data/raw',
        'data/extracted', 
        'data/chunks',
        'data/embeddings'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("⚠️  Some data directories are missing:")
        for dir_path in missing_dirs:
            print(f"   - {dir_path}")
        print("\n💡 These will be created automatically when you run the pipeline.")
        print("   Add PDF files to data/raw/ and run the preprocessing scripts.")
    
    return True

def launch_app():
    """Launch the Streamlit app"""
    print("\n" + "="*60)
    print("🚀 LAUNCHING AI LEGAL REFERENCE SYSTEM")
    print("="*60)
    print("📱 Opening in your default browser...")
    print("🔗 URL: http://localhost:8501")
    print("\n⚖️ AI Legal Assistant is ready!")
    print("💡 Ask questions about Indian laws, IPC sections, and legal procedures")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Launch Streamlit with optimized settings
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost", 
            "--browser.gatherUsageStats=false",
            "--server.headless=false",
            "--server.runOnSave=true"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 AI Legal Assistant stopped. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error launching Streamlit: {e}")
        print("💡 Try running manually: streamlit run app.py")
    except FileNotFoundError:
        print("\n❌ Streamlit not found!")
        print("📦 Install with: pip install streamlit")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def main():
    """Main launcher function"""
    print("="*60)
    print("⚖️  AI LEGAL REFERENCE SYSTEM LAUNCHER")
    print("="*60)
    print("🔍 Performing system checks...")
    
    # Check if app.py exists
    if not Path('app.py').exists():
        print("❌ app.py not found in current directory!")
        print("💡 Make sure you're in the correct project directory.")
        return
    
    # Check requirements
    print("\n📦 Checking Python packages...")
    if not check_requirements():
        print("\n❌ Package check failed!")
        print("💡 Install required packages and try again.")
        return
    
    print("✅ All required packages installed")
    
    # Check environment file
    print("\n🔐 Checking environment configuration...")
    if not check_env_file():
        print("\n❌ Environment check failed!")
        print("💡 Configure your .env file and try again.")
        return
    
    print("✅ Environment configured correctly")
    
    # Check data structure
    print("\n📁 Checking data structure...")
    check_data_structure()
    
    print("\n✅ System ready!")
    
    # Launch the app
    launch_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Launcher interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Launcher error: {e}")
        print("💡 Please check your setup and try again.")