import streamlit as st
import requests
import uuid
import os
from typing import List, Dict

# FastAPI backend URL
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Inter:wght@400;500;600&display=swap');
        
        :root {
            --bg-main: #05070a;
            --sidebar-bg: rgba(10, 15, 25, 0.85);
            --accent-primary: #3b82f6;
            --accent-secondary: #8b5cf6;
            --glass-card: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
        }

        .stApp {
            background-color: var(--bg-main);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg);
            backdrop-filter: blur(30px);
            border-right: 1px solid var(--glass-border);
        }

        /* Titles and Typography */
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            letter-spacing: -0.02em;
        }
        
        .main-title {
            font-size: 2.8rem;
            font-weight: 600;
            background: linear-gradient(to right, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }

        /* Conversation List Buttons */
        .stButton > button {
            border-radius: 12px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--text-secondary);
            text-align: left;
            padding: 10px 15px;
            transition: all 0.2s ease;
            width: 100%;
        }

        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            border-color: var(--glass-border);
        }

        /* Active Chat Button Highlight */
        .active-chat {
            background: rgba(59, 130, 246, 0.1) !important;
            border-color: rgba(59, 130, 246, 0.3) !important;
            color: #60a5fa !important;
        }

        /* New Chat Button */
        .new-chat-btn button {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
        }

        .new-chat-btn button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        }

        /* Chat Message Cards */
        .stChatMessage {
            background: var(--glass-card);
            border: 1px solid var(--glass-border);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 1.2rem;
            transition: border-color 0.3s ease;
        }
        
        /* Specific styling for user messages to make them pop */
        [data-testid="stChatMessageUser"] {
            background: rgba(59, 130, 246, 0.05);
            border-color: rgba(59, 130, 246, 0.1);
        }

        /* Avatar styling */
        [data-testid="stChatMessageAvatarUser"] {
            border: 2px solid var(--accent-primary);
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            border: 2px solid var(--accent-secondary);
        }

        /* Chat input refinement */
        [data-testid="stChatInput"] {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(10px);
        }

        /* Thinking state */
        .stSpinner > div {
            border-top-color: var(--accent-primary) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def fetch_conversations() -> List[Dict]:
    try:
        resp = requests.get(f"{BASE_URL}/conversations")
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def create_new_conversation_id() -> str:
    # We generate a UUID locally. It only gets persisted in the DB 
    # when the first message is sent via /ask.
    return str(uuid.uuid4())

def fetch_messages(conversation_id: str) -> List[Dict]:
    try:
        resp = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def send_question(conversation_id: str, question: str) -> str:
    try:
        resp = requests.post(
            f"{BASE_URL}/ask",
            json={"conversation_id": conversation_id, "question": question}
        )
        return resp.json().get("answer", "Error: No answer returned.")
    except Exception as e:
        return f"Error connecting to backend: {e}"

def delete_conversation(conversation_id: str):
    try:
        resp = requests.delete(f"{BASE_URL}/conversations/{conversation_id}")
        return resp.status_code == 200
    except:
        return False

def main():
    st.set_page_config(page_title="AI QA", page_icon="💎", layout="wide")
    apply_custom_styles()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # URL persistence: check for 'cid' in query params
    query_params = st.query_params
    url_cid = query_params.get("cid", "")
    
    # Initialize session state conversation_id if not present
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = ""

    # Fetch available conversations to check if URL cid is valid or to auto-select
    conversations = fetch_conversations()

    # Startup logic for conversation selection
    if not st.session_state.conversation_id:
        if url_cid:
            # If URL has a CID, try to load it
            st.session_state.conversation_id = url_cid
            st.session_state.messages = fetch_messages(url_cid)
        elif conversations:
            # Otherwise, auto-select the most recent one from history
            latest_cid = conversations[0]['conversation_id']
            st.session_state.conversation_id = latest_cid
            st.session_state.messages = fetch_messages(latest_cid)
            st.query_params["cid"] = latest_cid
        else:
            # No history and no URL CID, start a fresh local ID
            # IMPORTANT: We don't write to DB yet! Only on first message.
            st.session_state.conversation_id = create_new_conversation_id()
            st.session_state.messages = []

    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='padding: 10px 0;'>💎 History</h2>", unsafe_allow_html=True)
        
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
        if st.button("➕ Start New Chat", use_container_width=True):
            new_id = create_new_conversation_id()
            st.session_state.conversation_id = new_id
            st.session_state.messages = []
            st.query_params["cid"] = new_id
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        
        if not conversations:
            st.info("No saved chats yet.")
        
        for chat in conversations:
            cols = st.columns([0.8, 0.2])
            cid = chat['conversation_id']
            title = chat['title']
            is_active = st.session_state.get("conversation_id") == cid
            
            with cols[0]:
                btn_label = f"✨ {title}" if is_active else f"📝 {title}"
                if st.button(btn_label, key=f"btn_{cid}", use_container_width=True):
                    st.session_state.conversation_id = cid
                    st.session_state.messages = fetch_messages(cid)
                    st.query_params["cid"] = cid
                    st.rerun()
            
            with cols[1]:
                if st.button("🗑️", key=f"del_{cid}", help="Delete this chat"):
                    if delete_conversation(cid):
                        if is_active:
                            # Clear session and params after deleting active chat
                            st.session_state.conversation_id = ""
                            if "cid" in st.query_params:
                                del st.query_params["cid"]
                        st.rerun()

    # Main Chat Area
    st.markdown('<h1 class="main-title">AI QA Assistant</h1>', unsafe_allow_html=True)
    st.caption("A high-performance intelligent interface with persistent memory.")

    # Refresh current ID in session state if it changed in URL without rerun
    if url_cid and url_cid != st.session_state.conversation_id:
        st.session_state.conversation_id = url_cid
        st.session_state.messages = fetch_messages(url_cid)

    # Display Conversations
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Message your AI assistant..."):
        # Local show
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant thinking
        with st.chat_message("assistant"):
            with st.spinner(" "): 
                answer = send_question(st.session_state.conversation_id, prompt)
                st.markdown(answer)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()
