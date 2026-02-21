import streamlit as st
import os
from dotenv import load_dotenv
import random
import html
import time
import base64

# Load environment variables first
load_dotenv()

# Page configuration must be first
st.set_page_config(page_title="AI Legal Assistant", page_icon="⚖️", layout="wide")

# Import authentication functions
try:
    from auth_backend import init_user_db, signup_user, login_user, get_user_details, change_password, delete_user_account
    from chat_manager import create_new_chat, get_user_chats, load_chat_messages, save_chat_messages, delete_chat, update_chat_title
    auth_available = True
except ImportError as e:
    auth_available = False
    # Fallback functions
    def init_user_db(): return True
    def signup_user(e, u, p): return True, "Account created successfully (Demo Mode)"
    def login_user(u, p): return True, "Login successful (Demo Mode)"
    def create_new_chat(user): return f"demo_chat_{hash(user) % 10000}"
    def get_user_chats(user): return []
    def load_chat_messages(chat_id): return [{"role":"assistant","content":"How can I help you with Indian legal matters?"}]
    def save_chat_messages(chat_id, messages): return True
    def delete_chat(chat_id, user): return True
    def update_chat_title(chat_id, user, title): return True

# Initialize the database
if auth_available:
    init_user_db()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with Indian legal matters?"}]
if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"
if "auth_theme" not in st.session_state:
    st.session_state.auth_theme = "Dark"
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "user_chats" not in st.session_state:
    st.session_state.user_chats = []
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "show_profile" not in st.session_state:
    st.session_state.show_profile = False
if "response_mode" not in st.session_state:
    st.session_state.response_mode = "Local (No API Required)"

unique_css_key = random.randint(0, 99999)

def get_base64_image(path):
    """Convert image to base64 string"""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# ---------------------------------------------------------------------
# 💬 Chat Session Management Functions
# ---------------------------------------------------------------------
def load_chat_session(chat_id):
    """Load a specific chat session"""
    try:
        # Save current before switching
        if st.session_state.current_chat_id and st.session_state.current_chat_id != chat_id:
            save_chat_messages(st.session_state.current_chat_id, st.session_state.messages)
        
        messages = load_chat_messages(chat_id)
        if messages:
            st.session_state.messages = messages
            st.session_state.current_chat_id = chat_id
        else:
            # Fallback if no messages found
            st.session_state.messages = [
                {"role": "assistant", "content": "How can I help you with Indian legal matters?"}
            ]
            st.session_state.current_chat_id = chat_id
    except Exception as e:
        st.error(f"Error loading chat: {e}")


def create_new_chat_session():
    """Create a new chat session"""
    # Save current before creating new
    if st.session_state.current_chat_id and st.session_state.messages:
        save_chat_messages(st.session_state.current_chat_id, st.session_state.messages)

    try:
        chat_id = create_new_chat(st.session_state.username)
        if chat_id:
            # Reset to fresh chat state
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = [
                {"role": "assistant", "content": "How can I help you with Indian legal matters?"}
            ]
            # Refresh chat history immediately
            st.session_state.user_chats = get_user_chats(st.session_state.username)
            st.rerun()
    except Exception as e:
        st.error(f"Error creating new chat: {e}")


def delete_chat_session(chat_id):
    """Delete a chat session"""
    try:
        ok = delete_chat(chat_id, st.session_state.username)
    except Exception:
        ok = False

    if ok:
        # Refresh chat list immediately
        st.session_state.user_chats = get_user_chats(st.session_state.username)

        # If deleted chat was current
        if st.session_state.current_chat_id == chat_id:
            if st.session_state.user_chats:
                # Load the first available chat
                st.session_state.current_chat_id = st.session_state.user_chats[0]["_id"]
                messages = load_chat_messages(st.session_state.current_chat_id)
                st.session_state.messages = messages if messages else [
                    {"role": "assistant", "content": "How can I help you with Indian legal matters?"}
                ]
            else:
                # No chats left, create a new one
                create_new_chat_session()
                return  # create_new_chat_session handles rerun

        st.rerun()

# ---------------------------------------------------------------------
# 🧠 Initialize session state for chat
# ---------------------------------------------------------------------
def render_chat_history_sidebar():
    """Renders the left sidebar with user chat history"""
    st.markdown("#### 💬 Chat History")

    if st.button("➕ New Chat", use_container_width=True):
        # Save current chat before creating new one
        if st.session_state.current_chat_id and len(st.session_state.messages) > 1:
            save_chat_messages(st.session_state.current_chat_id, st.session_state.messages)
        create_new_chat_session()

    st.divider()

    # Always refresh chat list when logged in
    if st.session_state.logged_in and st.session_state.username:
        st.session_state.user_chats = get_user_chats(st.session_state.username)

    if st.session_state.user_chats:
        for chat in st.session_state.user_chats:
            chat_id = chat["_id"]
            # Use title if available, otherwise first_message
            display_text = chat.get("title", chat.get("first_message", "New Chat"))
            
            # Truncate long titles
            if len(display_text) > 25:
                display_text = display_text[:25] + "..."

            col1, col2 = st.columns([4, 1])
            with col1:
                is_active = chat_id == st.session_state.current_chat_id
                if st.button(
                    display_text,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    if chat_id != st.session_state.current_chat_id:
                        # Save current before switching
                        if st.session_state.current_chat_id and len(st.session_state.messages) > 1:
                            save_chat_messages(st.session_state.current_chat_id, st.session_state.messages)
                        load_chat_session(chat_id)
                        st.rerun()

            with col2:
                if st.button("❌", key=f"delete_{chat_id}"):
                    delete_chat_session(chat_id)
    else:
        st.info("No chat history yet. Start a new conversation!")

@st.cache_resource
def load_assistant():
    try:
        from scripts.enhanced_legal_assistant_QA import EnhancedLegalAssistant
        return EnhancedLegalAssistant()
    except Exception as e:
        st.error(f"❌ Failed to initialize Legal Assistant: {e}")
        return None

# Don't load assistant immediately - load only when needed
assistant = None

# Theme definitions
THEMES = {
    "Dark": {
        "bg": "#000000", "text": "#FEFEFE",
        "sidebar": "#07071B", "sidebar_text": "#FFFFFF", "sidebar_border": "#3E3E4E",
        "subtitle": "#B2BEC3", "user_bg": "#FC6500", "user_text": "#FFFFFF",
        "bot_bg": "#610101", "bot_text": "#FFFFFF", "button": "#F1C40F",
        "button_hover": "#FF4646", "input_bg": "#3C3C4E", "quick_btn_bg": "#120202",
        "quick_btn_text": "#F5F6FA", "highlight": "#F9E79F", "border": "#333333"
    },
    "Light": {
        "bg": "#FFFEE5", "text": "#2D3436",
        "sidebar": "#F5F7FA", "sidebar_text": "#2C3E50", "sidebar_border": "#D5DBDB",
        "subtitle": "#636E72", "user_bg": "#0048FF", "user_text": "#FFFFFF",
        "bot_bg": "#FC6500", "bot_text": "#FFFFFF", "button": "#F39C12",
        "button_hover": "#FC9300", "input_bg": "#FFFEE5", "quick_btn_bg": "#FFFFFF",
        "quick_btn_text": "#34495E", "highlight": "#F1C40F", "border": "#DDDDDD"
    },
    "Ocean": {
        "bg": "#02182E", "text": "#FFFFFF",
        "sidebar": "#003366", "sidebar_text": "#B3E5FC", "sidebar_border": "#005F99",
        "subtitle": "#A9CCE3", "user_bg": "#0277BD", "user_text": "#E3F2FD",
        "bot_bg": "#02A5AB", "bot_text": "#E0F7FA", "button": "#03A9F4",
        "button_hover": "#1C9EB6", "input_bg": "#002B5B", "quick_btn_bg": "#004D73",
        "quick_btn_text": "#E1F5FE", "highlight": "#81D4FA", "border": "#003a63"
    },
    "Forest": {
        "bg": "#05311F", "text": "#E9F5DB",
        "sidebar": "#2D6A4F", "sidebar_text": "#B7E4C7", "sidebar_border": "#40916C",
        "subtitle": "#95D5B2", "user_bg": "#00C35B", "user_text": "#FFFFFF",
        "bot_bg": "#74C69D", "bot_text": "#1B4332", "button": "#00FF22",
        "button_hover": "#00C35B", "input_bg": "#2D6A4F", "quick_btn_bg": "#40916C",
        "quick_btn_text": "#FFFFFF", "highlight": "#B7E4C7", "border": "#2f5e46"
    },
    "Crimson": {
        "bg": "#270606", "text": "#FFEAEA",
        "sidebar": "#400000", "sidebar_text": "#FFB3B3", "sidebar_border": "#590000",
        "subtitle": "#FFCCCC", "user_bg": "#FF0000", "user_text": "#FFFFFF",
        "bot_bg": "#C9333F", "bot_text": "#FFEAEA", "button": "#C70039",
        "button_hover": "#FA2E57", "input_bg": "#590000", "quick_btn_bg": "#400000",
        "quick_btn_text": "#FFB3B3", "highlight": "#FFAAAA", "border": "#4a0000"
    }
}

colors = THEMES.get(st.session_state["theme"], THEMES["Dark"])

# Apply theme styles
st.markdown(f"""
<style id="theme-style-{unique_css_key}">
html, body, [class*="stAppViewContainer"] {{
    background-color: {colors['bg']} !important;
    color: {colors['text']} !important;
    transition: background-color 0.18s ease, color 0.18s ease;
}}
[data-testid="stSidebar"] {{
    background-color: {colors['sidebar']} !important;
    color: {colors['sidebar_text']} !important;
    border-right: 1px solid {colors['sidebar_border']} !important;
}}
[data-testid="stSidebar"] * {{
    color: {colors['sidebar_text']} !important;
}}
div[data-baseweb="select"] div, 
div[data-baseweb="select"] span, 
div[role="combobox"], 
div[role="combobox"] * {{
    color: black !important;
}}
.stTextInput > div > div > input {{
    background-color: {colors['input_bg']} !important;
    color: {colors['text']} !important;
    border-radius: 8px !important;
}}
.stButton > button {{
    background-color: {colors['quick_btn_bg']} !important;
    color: {colors['quick_btn_text']} !important;
    border-radius: 8px !important;
    border: 1px solid {colors['border']} !important;
}}
.stButton > button:hover {{
    background-color: {colors['button_hover']} !important;
    color: white !important;
}}
.stMarkdown a {{ color: {colors['highlight']} !important; }}

/* Force all sidebar buttons to have consistent styling */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] div button,
[data-testid="stSidebar"] * button {{
    background: {colors['quick_btn_bg']} !important;
    background-color: {colors['quick_btn_bg']} !important;
    color: {colors['quick_btn_text']} !important;
    border: 1px solid {colors['border']} !important;
    border-radius: 8px !important;
}}
/* General button hover - exclude delete buttons */
[data-testid="stSidebar"] button:not([key*="delete_"]):hover,
[data-testid="stSidebar"] .stButton > button:not([key*="delete_"]):hover {{
    background: {colors['button_hover']} !important;
    background-color: {colors['button_hover']} !important;
    color: white !important;
}}
/* Ultra-specific delete button hover - maximum priority */
[data-testid="stSidebar"] button[key*="delete_"]:hover,
[data-testid="stSidebar"] .stButton > button[key*="delete_"]:hover,
[data-testid="stSidebar"] div[data-testid="column"] button[key*="delete_"]:hover,
[data-testid="stSidebar"] div button[key*="delete_"]:hover,
[data-testid="stSidebar"] * button[key*="delete_"]:hover {{
    background: #FFD700 !important;
    background-color: #FFD700 !important;
    color: #000000 !important;
    border: 1px solid #FFA500 !important;
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
    transition: all 0.3s ease !important;
}}
/* Reduce spacing between chat items */
[data-testid="stSidebar"] .element-container {{
    margin-bottom: 0.1rem !important;
}}

/* Center symbols in chat list columns */
[data-testid="stSidebar"] [data-testid="column"]:nth-child(2) button,
[data-testid="stSidebar"] [data-testid="column"]:nth-child(3) button {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    min-height: 20px !important;
    max-height: 20px !important;
    height: 20px !important;
    font-size: 8px !important;
    line-height: 1 !important;
    overflow: hidden !important;
    width: 20px !important;
    max-width: 20px !important;
    min-width: 20px !important;
    box-sizing: border-box !important;
    margin: 0 auto !important;
    border-radius: 50% !important;
    font-weight: bold !important;
}}
</style>
""", unsafe_allow_html=True)

# Authentication page
def show_auth_page():
    """Simple compact authentication page"""
    
    # Theme colors
    if st.session_state.auth_theme == "Dark":
        bg = "#020024"
        text = "#ffffff"
        accent = "linear-gradient(90deg,rgba(2, 0, 36, 1) 0%, rgba(9, 9, 121, 1) 35%, rgba(0, 212, 255, 1) 100%)"
    else:
        bg = "#fdedaf"
        text = "#000000"
        accent = "linear-gradient(135deg, #FFD700, #FFA500)"

    # Theme toggle
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("☀" if st.session_state.auth_theme == "Dark" else "☪", key="theme_btn"):
            st.session_state.auth_theme = "Light" if st.session_state.auth_theme == "Dark" else "Dark"
            st.rerun()

    # Title
    st.markdown("<h1 style='text-align: center;'>⚖️ AI Legal Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Your Expert Legal AI Companion</p>", unsafe_allow_html=True)
    
    # Try to load local images, fallback to placeholder
    img_paths = [
        "images/legal_img-4.png",
        "images/legal_img-10.png", 
        "images/legal_img-5.png",
        "images/legal_img-9.png",
        "images/legal_img-3.png"
    ]
    
    fallback_urls = [
        "https://via.placeholder.com/100x100/FFD700/000000?text=⚖️",
        "https://via.placeholder.com/100x100/FFA500/000000?text=📚",
        "https://via.placeholder.com/100x100/32CD32/000000?text=📋",
        "https://via.placeholder.com/100x100/FF6B35/000000?text=🏛️",
        "https://via.placeholder.com/100x100/4ECDC4/000000?text=📖"
    ]
    
    # Generate image sources (base64 or fallback URLs)
    img_sources = []
    for i, path in enumerate(img_paths):
        base64_img = get_base64_image(path)
        if base64_img:
            img_sources.append(f"data:image/png;base64,{base64_img}")
        else:
            img_sources.append(fallback_urls[i])
    
    # Add floating banner animation with proper background inheritance
    st.markdown(f"""
    <style>
    /* Container for floating items - inherits page background */
    .floating-banner {{
        position: relative;
        width: 100%;
        height: 180px;
        background: {bg} !important;
        background-color: {bg} !important;
        overflow: hidden;
        margin-bottom: 20px;
    }}
    
    /* Each image floats individually */
    .floating-item {{
        position: absolute;
        width: 100px;
        opacity: 0.9;
        animation: floatAround 25s ease-in-out infinite;
    }}
    
    /* Keyframe motion (gentle drifting) */
    @keyframes floatAround {{
        0% {{ transform: translate(0px, 0px) rotate(0deg); }}
        25% {{ transform: translate(30px, -20px) rotate(3deg); }}
        50% {{ transform: translate(-20px, 25px) rotate(-2deg); }}
        75% {{ transform: translate(25px, 15px) rotate(2deg); }}
        100% {{ transform: translate(0px, 0px) rotate(0deg); }}
    }}
    
    /* Make them move at slightly different speeds */
    .floating-item:nth-child(1) {{ top: 20px; left: 10%; animation-duration: 26s; }}
    .floating-item:nth-child(2) {{ top: 60px; left: 35%; animation-duration: 30s; }}
    .floating-item:nth-child(3) {{ top: 40px; left: 55%; animation-duration: 24s; }}
    .floating-item:nth-child(4) {{ top: 30px; left: 75%; animation-duration: 28s; }}
    .floating-item:nth-child(5) {{ top: 80px; left: 90%; animation-duration: 32s; }}
    </style>
    """, unsafe_allow_html=True)
    
    # Add main styling with comprehensive background coverage
    st.markdown(f"""
    <style>
    /* Force background on all elements */
    html, body, [class*="css"], [data-testid="stAppViewContainer"], 
    .stApp, .main, .block-container, [class*="stAppViewContainer"] {{
        background: {bg} !important;
        background-color: {bg} !important;
        color: {text} !important;
    }}
    
    /* Hide sidebar on login page */
    [data-testid="stSidebar"] {{ display: none !important; }}
    
    /* Center the login form */
    .main .block-container {{
        max-width: 600px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
        position: relative;
        z-index: 1;
        background: {bg} !important;
    }}
    
    /* Style form elements */
    .stTextInput > label, .stTab label, h1, h2, h3, p {{
        color: {text} !important;
    }}
    
    .stButton > button {{
        background: {accent} !important;
        color: #000 !important;
        width: 100% !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 12px 16px !important;
        margin: 8px 0 !important;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        background: {bg} !important;
        gap: 12px !important;
        padding: 8px !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {text} !important;
        background: {bg} !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        padding: 12px 24px !important;
        margin: 0 6px !important;
        border: 2px solid transparent !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: {accent} !important;
        color: #000000 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {accent} !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: 2px solid rgba(255,255,255,0.5) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }}
    
    /* Input fields - black text for better readability */
    .stTextInput > div > div > input {{
        background-color: rgba(255,255,255,0.9) !important;
        color: #000000 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Add floating banner
    st.markdown(f"""
    <div class="floating-banner">
      <img src="{img_sources[0]}" class="floating-item">
      <img src="{img_sources[1]}" class="floating-item">
      <img src="{img_sources[2]}" class="floating-item">
      <img src="{img_sources[3]}" class="floating-item">
      <img src="{img_sources[4]}" class="floating-item">
    </div>
    """, unsafe_allow_html=True)

    # Centered login container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

        with tab1:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Continue", key="login_btn", use_container_width=True):
                if username and password:
                    success, msg = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        # Load user's chat history
                        st.session_state.user_chats = get_user_chats(username)
                        # Always start with a fresh chat on login
                        chat_id = create_new_chat(username)
                        if chat_id:
                            st.session_state.current_chat_id = chat_id
                            st.session_state.messages = [
                                {"role": "assistant", "content": "How can I help you with Indian legal matters?"}
                            ]
                            # Refresh chat list to include the new chat
                            st.session_state.user_chats = get_user_chats(username)
                        
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter both username and password.")
            
            # Get Started button
            st.markdown("<br>", unsafe_allow_html=True)
            col_center = st.columns([1, 2, 1])[1]
            with col_center:
                if st.button(" Get Started!", key="get_started_btn", use_container_width=True):
                    # Switch to signup tab by using JavaScript
                    st.markdown("""
                    <script>
                    const tabs = parent.document.querySelectorAll('[data-baseweb="tab"]');
                    if (tabs.length > 1) tabs[1].click();
                    </script>
                    """, unsafe_allow_html=True)
                    st.info("👆 Click on the 'Sign Up' tab above to create your account!")

        with tab2:
            email = st.text_input("Email", key="signup_email")
            new_username = st.text_input("Username", key="signup_username")
            new_password = st.text_input("Password", type="password", key="signup_password")
            
            if st.button("Create Account", key="signup_btn", use_container_width=True):
                if email and new_username and new_password:
                    success, msg = signup_user(email, new_username, new_password)
                    if success:
                        st.success(msg)
                        st.info("Please switch to Login tab to sign in.")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all fields.")
    


# Check authentication before showing main app
if not st.session_state.logged_in:
    show_auth_page()
    st.stop()

# Sidebar: Chat History Management
with st.sidebar:
    st.markdown("### ⚖️ AI Legal Assistant")
    st.markdown("*Your Expert Legal Companion*")
    
    # User info with profile button and logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Welcome, {st.session_state.username}!** 👋")
    with col2:
        if st.button("👤", key="profile_btn", help="Profile Settings"):
            st.session_state.show_profile = not st.session_state.show_profile
            st.rerun()
    
    # Profile Modal
    if st.session_state.show_profile:
        st.markdown("---")
        st.markdown("### 👤 Profile Settings")
        
        # Get user details
        user_details = get_user_details(st.session_state.username)
        
        if user_details:
            st.markdown(f"**Email:** {user_details['email']}")
            st.markdown(f"**Username:** {user_details['username']}")
            st.markdown(f"**Member since:** {user_details['created_at'][:10]}")
            
            st.markdown("---")
            
            # Change Password Section
            if st.button("🔐 Change Password", use_container_width=True):
                st.session_state.show_change_password = True
                st.rerun()
            
            # Delete Account Section
            if st.button("⚠️ Delete Account", use_container_width=True):
                st.session_state.show_delete_account = True
                st.rerun()
            
            # Close Profile
            if st.button("⤫ &nbsp;&nbsp; Close Settings", use_container_width=True):
                st.session_state.show_profile = False
                st.rerun()
        else:
            st.error("Could not load user details")
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Change Password Modal
    if st.session_state.get("show_change_password", False):
        st.markdown("---")
        st.markdown("### 🔐 Change Password")
        
        current_pwd = st.text_input("Current Password", type="password", key="current_pwd")
        new_pwd = st.text_input("New Password", type="password", key="new_pwd")
        confirm_pwd = st.text_input("Confirm New Password", type="password", key="confirm_pwd")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Password", key="update_pwd_btn"):
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("Please fill all fields")
                elif new_pwd != confirm_pwd:
                    st.error("New passwords don't match")
                elif len(new_pwd) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, msg = change_password(st.session_state.username, current_pwd, new_pwd)
                    if success:
                        st.success(msg)
                        st.session_state.show_change_password = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
        
        with col2:
            if st.button("Cancel", key="cancel_pwd_btn"):
                st.session_state.show_change_password = False
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Delete Account Modal
    if st.session_state.get("show_delete_account", False):
        st.markdown("---")
        st.markdown("### ⚠️ Delete Account")
        st.warning("This action cannot be undone!")
        
        delete_pwd = st.text_input("Enter your password to confirm", type="password", key="delete_pwd")
        confirm_delete = st.checkbox("I understand this will permanently delete my account")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Account", key="confirm_delete_btn", type="primary"):
                if not delete_pwd:
                    st.error("Please enter your password")
                elif not confirm_delete:
                    st.error("Please confirm account deletion")
                else:
                    success, msg = delete_user_account(st.session_state.username, delete_pwd)
                    if success:
                        st.success(msg)
                        # Clear session and logout
                        st.session_state.logged_in = False
                        st.session_state.username = ""
                        st.session_state.messages = []
                        st.session_state.active_chat_id = None
                        st.session_state.user_chats = []
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(msg)
        
        with col2:
            if st.button("Cancel", key="cancel_delete_btn"):
                st.session_state.show_delete_account = False
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(" Logout &nbsp;&nbsp; ➜]", use_container_width=True):
        # Save current chat before logout
        if st.session_state.active_chat_id and st.session_state.messages:
            save_chat_messages(st.session_state.active_chat_id, st.session_state.messages)
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.messages = []
        st.session_state.active_chat_id = None
        st.session_state.user_chats = []
        st.rerun()

    # Button: Start New Chat
    if st.button("➕ New Chat", use_container_width=True):
        # Auto-save current chat before switching
        if st.session_state.active_chat_id and st.session_state.messages:
            save_chat_messages(st.session_state.active_chat_id, st.session_state.messages)

        new_id = create_new_chat(st.session_state.username)
        st.session_state.active_chat_id = new_id
        st.session_state.messages = load_chat_messages(new_id)
        st.rerun()
    
    st.divider()
    
    # Response Mode Selector
    st.markdown("### ⚙️ Response Mode")
    mode_options = [
        "Local (No API Required)",
        "OpenAI (Requires API Key)"
    ]
    selected_mode = st.selectbox(
        "🤖 Choose AI Mode",
        mode_options,
        index=mode_options.index(st.session_state.response_mode),
        help="Local mode works without OpenAI. OpenAI mode provides conversational answers."
    )
    
    if selected_mode != st.session_state.response_mode:
        st.session_state.response_mode = selected_mode
        st.rerun()
    
    # Show mode status - only show warning if OpenAI mode is selected
    if st.session_state.response_mode == "Local (No API Required)":
        st.success("✅ Local Mode Active")
    else:
        # Only check OpenAI availability when OpenAI mode is selected
        if assistant and hasattr(assistant, 'openai_available') and assistant.openai_available:
            st.success("✅ OpenAI Mode Active")
        else:
            st.warning("⚠️ OpenAI unavailable. Switch to Local Mode or check API key.")
    
    st.divider()
    
    # Theme selector
    theme_keys = list(THEMES.keys())
    idx = theme_keys.index(st.session_state["theme"]) if st.session_state["theme"] in theme_keys else 0
    theme_choice = st.selectbox("🎨 Choose Theme", theme_keys, index=idx)
    if theme_choice != st.session_state["theme"]:
        st.session_state["theme"] = theme_choice
        st.rerun()
    
    st.divider()
    
    st.markdown("### ⌯⌲ Chat History")

    # Load user chats
    user_chats = get_user_chats(st.session_state.username)


    # Display user's past chats
    for chat in user_chats:
        col1, col2, col3 = st.columns([5, 0.7, 0.7])

        # Select chat
        if col1.button(chat.get("title", "New Chat"), key=f"select_{chat['_id']}", use_container_width=True):
            # Auto-save current chat before switching
            if st.session_state.active_chat_id and st.session_state.messages:
                save_chat_messages(st.session_state.active_chat_id, st.session_state.messages)

            st.session_state.active_chat_id = chat["_id"]
            st.session_state.messages = load_chat_messages(chat["_id"])
            st.rerun()

        # Rename button
        if col2.button("✦", key=f"rename_{chat['_id']}", help="Rename chat"):
            # Simple rename using session state
            if f"rename_input_{chat['_id']}" not in st.session_state:
                st.session_state[f"rename_input_{chat['_id']}"] = True

        # Delete button
        if col3.button("X", key=f"delete_{chat['_id']}", help="Delete chat"):
            delete_chat(chat["_id"], st.session_state.username)
            if st.session_state.active_chat_id == chat["_id"]:
                st.session_state.active_chat_id = None
                st.session_state.messages = []
            st.rerun()
        
        # Show rename input if activated
        if st.session_state.get(f"rename_input_{chat['_id']}", False):
            new_title = st.text_input("New title:", value=chat.get("title", "New Chat"), key=f"title_input_{chat['_id']}")
            col_save, col_cancel = st.columns(2)
            if col_save.button("Save", key=f"save_{chat['_id']}"):
                if new_title:
                    update_chat_title(chat["_id"], st.session_state.username, new_title)
                st.session_state[f"rename_input_{chat['_id']}"] = False
                st.rerun()
            if col_cancel.button("Cancel", key=f"cancel_{chat['_id']}"):
                st.session_state[f"rename_input_{chat['_id']}"] = False
                st.rerun()
    
    st.divider()
    
    st.markdown("#### 💡 Quick Questions")
    queries = [
        "What is IPC Section 302?",
        "Explain theft under Indian law",
        "What are the stages of a trial?",
        "What is criminal breach of trust?",
        "Explain fundamental rights"
    ]
    for i, q in enumerate(queries):
        if st.button(q, key=f"q_{i}", use_container_width=True):
            # Ensure we have an active chat
            if not st.session_state.active_chat_id:
                new_id = create_new_chat(st.session_state.username)
                st.session_state.active_chat_id = new_id
                st.session_state.messages = load_chat_messages(new_id)
            
            # Add user message
            user_msg = {"role": "user", "content": q}
            st.session_state.messages.append(user_msg)
            
            # Load assistant only when needed
            if assistant is None:
                with st.spinner("🤖 Loading AI Assistant..."):
                    assistant = load_assistant()
            
            if assistant:
                with st.spinner("⚖️ Analyzing legal documents..."):
                    matches = assistant.retrieve_context(q, top_k=5)
                    # Use selected mode
                    mode = "local" if st.session_state.response_mode == "Local (No API Required)" else "openai"
                    answer_data = assistant.format_legal_answer(q, matches, mode=mode)
                
                if "error" in answer_data:
                    # Show error in chat
                    error_msg = answer_data["error"]
                    assistant_msg = {"role": "assistant", "content": error_msg}
                    st.session_state.messages.append(assistant_msg)
                    save_chat_messages(st.session_state.active_chat_id, [user_msg, assistant_msg])
                else:
                    # Use clean answer without formatting
                    assistant_msg = {"role": "assistant", "content": answer_data['answer']}
                    st.session_state.messages.append(assistant_msg)
                    
                    # Save messages to MongoDB
                    save_chat_messages(st.session_state.active_chat_id, [user_msg, assistant_msg])
                    
                    # Auto-generate title for new chats
                    if len(st.session_state.messages) == 3:  # assistant + user + assistant
                        title = q[:30] + "..." if len(q) > 30 else q
                        update_chat_title(st.session_state.active_chat_id, st.session_state.username, title)
            
            st.rerun()

# Chat rendering function
def render_message(role, content):
    safe = html.escape(content).replace("\n", "<br>")
    if role == "user":
        bg, text, align = colors["user_bg"], colors["user_text"], "flex-end"
        radius = "18px 18px 0 18px"
    else:
        bg, text, align = colors["bot_bg"], colors["bot_text"], "flex-start"
        radius = "18px 18px 18px 0"

    bubble = f"""
    <div style="display:flex; justify-content:{align}; margin:8px 0;">
      <div style="
        background-color:{bg};
        color:{text};
        padding:12px 16px;
        border-radius:{radius};
        max-width:75%;
        box-shadow:0 3px 8px rgba(0,0,0,0.15);
        font-size:15px;
        line-height:1.5;
      ">
        {safe}
      </div>
    </div>
    """
    st.markdown(bubble, unsafe_allow_html=True)

# Main chat area
st.markdown(f"""
<style>
.gradient-title {{
    text-align: center;
    font-size: 2.5em;
    font-weight: 800;
    background: linear-gradient(90deg, #FFD700, #FFB300, #FFA500);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    margin-top: 10px;
}}
.welcome-text {{
    text-align: center;
    font-size: 1.1em;
    opacity: 0.8;
    margin-top: 10px;
    margin-bottom: 20px;
}}
</style>

<div style="text-align: center;">
    <span class="gradient-title">⚖️ AI Legal Assistant</span>
    <div class="welcome-text">Welcome, {st.session_state.username}! 👋</div>
</div>
""", unsafe_allow_html=True)

st.caption("Ask questions about IPC, CrPC, or Constitutional law")

# Display chat messages
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])

# User input box - always visible
if user_query := st.chat_input("Type your legal question..."):
    # Ensure we have an active chat
    if not st.session_state.active_chat_id:
        new_id = create_new_chat(st.session_state.username)
        st.session_state.active_chat_id = new_id
        st.session_state.messages = load_chat_messages(new_id)
    
    # Load assistant only when user asks a question
    if assistant is None:
        with st.spinner("🤖 Loading AI Assistant..."):
            assistant = load_assistant()
    
    if not assistant:
        st.error("Assistant not initialized. Check your configuration.")
        st.stop()
        
    # Append user message
    user_msg = {"role": "user", "content": user_query}
    st.session_state.messages.append(user_msg)

    # Generate assistant reply
    query_lower = user_query.lower().strip()
    simple_greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'how are you']
    is_greeting = any(greeting in query_lower for greeting in simple_greetings) and len(user_query.split()) <= 3
    
    if is_greeting:
        # For greetings, don't retrieve documents
        with st.spinner("🤖 Thinking..."):
            try:
                mode = "local" if st.session_state.response_mode == "Local (No API Required)" else "openai"
                answer_data = assistant.format_legal_answer(user_query, [], mode=mode)
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
    else:
        # For legal queries, retrieve documents
        with st.spinner("⚖️ Analyzing legal documents..."):
            try:
                matches = assistant.retrieve_context(user_query, top_k=5)
                mode = "local" if st.session_state.response_mode == "Local (No API Required)" else "openai"
                answer_data = assistant.format_legal_answer(user_query, matches, mode=mode)
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

    if "error" in answer_data:
        error_msg = answer_data["error"]
        st.error(error_msg)
        # Also add error to chat history so user can see it
        assistant_msg = {"role": "assistant", "content": error_msg}
        st.session_state.messages.append(assistant_msg)
        st.rerun()
    else:
        response = answer_data["answer"]
        
        # Use clean response without formatting
        assistant_msg = {"role": "assistant", "content": response}
        st.session_state.messages.append(assistant_msg)

        # Save messages to MongoDB
        save_chat_messages(st.session_state.active_chat_id, [user_msg, assistant_msg])
        
        # Auto-generate title from first user message if it's a new chat
        if len(st.session_state.messages) == 3:  # assistant + user + assistant
            title = user_query[:30] + "..." if len(user_query) > 30 else user_query
            update_chat_title(st.session_state.active_chat_id, st.session_state.username, title)

    # Refresh UI
    st.rerun()

# Final styles - Main app theme application
st.markdown(f"""
<style>
/* Main app background and text */
html, body, [class*="css"], [data-testid="stAppViewContainer"], 
.stApp, .main, .block-container {{ 
    background-color: {colors['bg']} !important; 
    color: {colors['text']} !important; 
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{ 
    background-color: {colors['sidebar']} !important; 
    color: {colors['sidebar_text']} !important; 
}}

/* Select box text color fix */
div[data-baseweb="select"] div, 
div[data-baseweb="select"] span, 
div[role="combobox"], 
div[role="combobox"] * {{ 
    color: black !important; 
}}

/* Input fields in main app */
.stTextInput > div > div > input {{
    background-color: {colors['input_bg']} !important;
    color: {colors['text']} !important;
    border: 1px solid {colors['border']} !important;
}}

</style>
""", unsafe_allow_html=True)