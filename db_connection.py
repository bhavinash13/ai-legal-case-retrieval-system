"""
Shared Database Connection Module
Handles MongoDB connection and dependency management for the entire app
"""

import subprocess
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

# Try to import required packages, install if missing
try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    print("Installing pymongo...")
    if install_package("pymongo"):
        from pymongo import MongoClient
        from bson.objectid import ObjectId
        PYMONGO_AVAILABLE = True
    else:
        MongoClient = None
        ObjectId = None
        PYMONGO_AVAILABLE = False

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    print("Installing bcrypt...")
    if install_package("bcrypt"):
        import bcrypt
        BCRYPT_AVAILABLE = True
    else:
        bcrypt = None
        BCRYPT_AVAILABLE = False

# Global connection variables
client = None
db = None
users = None
chats = None

def init_database():
    """Initialize MongoDB connection"""
    global client, db, users, chats
    
    if not PYMONGO_AVAILABLE:
        print("ERROR: MongoDB dependencies not available")
        return False
    
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client["ai_legal_assistant"]
        users = db["users"]
        chats = db["chat_sessions"]
        
        # Test connection
        client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB successfully")
        return True
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        client = None
        db = None
        users = None
        chats = None
        return False

def get_collections():
    """Get database collections"""
    return {
        'users': users,
        'chats': chats,
        'bcrypt': bcrypt if BCRYPT_AVAILABLE else None,
        'ObjectId': ObjectId if PYMONGO_AVAILABLE else None,
        'available': PYMONGO_AVAILABLE and BCRYPT_AVAILABLE
    }

# Initialize on import
init_database()