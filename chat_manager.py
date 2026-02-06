"""
Chat History Management for AI Legal Assistant
Handles MongoDB operations for user chat sessions
"""

from datetime import datetime
from db_connection import get_collections

# Get database collections
db_collections = get_collections()
chats = db_collections['chats']
ObjectId = db_collections['ObjectId']
DEPENDENCIES_AVAILABLE = db_collections['available']

if chats is not None:
    print("SUCCESS: Chat Manager connected to MongoDB")
else:
    print("ERROR: Chat Manager connection failed")


# --------------------------------------------------
# Create new chat session
# --------------------------------------------------
def create_new_chat(username, title=None):
    """Create a new chat session"""
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return None
    try:
        if not title:
            title = f"Chat {datetime.now().strftime('%m/%d %H:%M')}"

        chat_data = {
            "username": username,
            "title": title,
            "messages": [
                {"role": "assistant", "content": "How can I help you with Indian legal matters?"}
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = chats.insert_one(chat_data)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating chat: {e}")
        return None


# --------------------------------------------------
# Get user chats (list for sidebar/history)
# --------------------------------------------------
def get_user_chats(username):
    """Return all chats for a user (summary only)"""
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return []

    try:
        results = chats.find({"username": username}).sort("updated_at", -1)
        user_chats = []
        for chat in results:
            first_user_msg = ""
            for msg in chat.get("messages", []):
                if msg.get("role") == "user":
                    first_user_msg = msg["content"][:40]
                    break

            user_chats.append({
                "_id": str(chat["_id"]),
                "title": chat.get("title", "Untitled"),
                "created_at": chat.get("created_at"),
                "updated_at": chat.get("updated_at"),
                "first_message": first_user_msg
            })
        return user_chats

    except Exception as e:
        print(f"Error fetching chats: {e}")
        return []


# --------------------------------------------------
# Load messages for a specific chat
# --------------------------------------------------
def load_chat_messages(chat_id):
    """Load full chat messages"""
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return []
    try:
        chat = chats.find_one({"_id": ObjectId(chat_id)})
        if chat:
            return chat.get("messages", [])
        return []
    except Exception as e:
        print(f"Error loading chat messages: {e}")
        return []


# --------------------------------------------------
# Save (append/update) messages in a chat
# --------------------------------------------------
def save_chat_messages(chat_id, new_messages, title=None):
    """
    Append one or more new messages to an existing chat.
    `new_messages` can be a single dict or a list of dicts.
    """
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return False
    try:
        if isinstance(new_messages, dict):
            new_messages = [new_messages]

        update_data = {"updated_at": datetime.utcnow()}
        if title:
            update_data["title"] = title

        result = chats.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$push": {"messages": {"$each": new_messages}},
                "$set": update_data
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error saving chat messages: {e}")
        return False



# --------------------------------------------------
# Delete a chat
# --------------------------------------------------
def delete_chat(chat_id, username):
    """Delete user’s chat"""
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return False
    try:
        result = chats.delete_one({
            "_id": ObjectId(chat_id),
            "username": username
        })
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False


# --------------------------------------------------
# Rename chat
# --------------------------------------------------
def update_chat_title(chat_id, username, new_title):
    """Rename chat title"""
    if not DEPENDENCIES_AVAILABLE or chats is None:
        return False
    try:
        result = chats.update_one(
            {"_id": ObjectId(chat_id), "username": username},
            {"$set": {"title": new_title, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating chat title: {e}")
        return False
