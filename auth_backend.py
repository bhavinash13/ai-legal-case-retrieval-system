from datetime import datetime
from db_connection import get_collections

# Get database collections
db_collections = get_collections()
users = db_collections['users']
bcrypt = db_collections['bcrypt']
DEPENDENCIES_AVAILABLE = db_collections['available']

def init_user_db():
    """Initialize MongoDB connection (no table creation needed)"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return False
    return True

def signup_user(email, username, password):
    """Register a new user with MongoDB"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return False, "Database connection failed or dependencies missing"
    
    try:
        # Check for duplicates
        if users.find_one({"username": username}):
            return False, "Username already exists"
        if users.find_one({"email": email}):
            return False, "Email already exists"
        
        # Hash password with bcrypt
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        
        # Insert user
        users.insert_one({
            "email": email,
            "username": username,
            "password_hash": hashed_pw.decode("utf-8"),
            "created_at": datetime.now().isoformat()
        })
        
        return True, "Account created successfully!"
    
    except Exception as e:
        print(f"Signup error: {e}")
        return False, "Signup failed. Please try again."

def login_user(username, password):
    """Authenticate user with MongoDB"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return False, "Database connection failed or dependencies missing"
    
    try:
        # Find user
        user = users.find_one({"username": username})
        if not user:
            return False, "Username not found"
        
        # Check password
        stored_hash = user["password_hash"].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return True, "Login successful!"
        else:
            return False, "Incorrect password"
    
    except Exception as e:
        print(f"Login error: {e}")
        return False, "Login failed. Please try again."

def get_user_details(username):
    """Get user details from MongoDB"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return None
    
    try:
        user = users.find_one({"username": username})
        if user:
            return {
                "email": user.get("email", ""),
                "username": user.get("username", ""),
                "created_at": user.get("created_at", "")
            }
        return None
    except Exception as e:
        print(f"Get user details error: {e}")
        return None

def change_password(username, current_password, new_password):
    """Change user password in MongoDB"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return False, "Database connection failed"
    
    try:
        # Verify current password
        user = users.find_one({"username": username})
        if not user:
            return False, "User not found"
        
        stored_hash = user["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(current_password.encode("utf-8"), stored_hash):
            return False, "Current password is incorrect"
        
        # Hash new password
        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        
        # Update password
        users.update_one(
            {"username": username},
            {"$set": {"password_hash": new_hash.decode("utf-8")}}
        )
        
        return True, "Password changed successfully!"
    
    except Exception as e:
        print(f"Change password error: {e}")
        return False, "Password change failed. Please try again."

def delete_user_account(username, password):
    """Delete user account from MongoDB"""
    if not DEPENDENCIES_AVAILABLE or users is None:
        return False, "Database connection failed"
    
    try:
        # Verify password before deletion
        user = users.find_one({"username": username})
        if not user:
            return False, "User not found"
        
        stored_hash = user["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return False, "Password is incorrect"
        
        # Delete user
        users.delete_one({"username": username})
        
        return True, "Account deleted successfully!"
    
    except Exception as e:
        print(f"Delete account error: {e}")
        return False, "Account deletion failed. Please try again."
