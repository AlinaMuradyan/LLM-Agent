import mysql.connector
from mysql.connector import Error
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from typing import List, Dict, Optional
import uuid
from datetime import datetime

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def ensure_conversation_exists(conversation_id: str, title: str = "New Chat"):
    """Check if a conversation exists, and if not, create it."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM conversations WHERE conversation_id = %s", (conversation_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO conversations (conversation_id, title) VALUES (%s, %s)",
                (conversation_id, title)
            )
            conn.commit()
        cursor.close()
        conn.close()

def create_conversation(title: str = "New Chat") -> str:
    conversation_id = str(uuid.uuid4())
    ensure_conversation_exists(conversation_id, title)
    return conversation_id

def list_conversations() -> List[Dict]:
    conversations = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Only select conversations that have at least one message
        query = """
            SELECT DISTINCT c.* 
            FROM conversations c
            JOIN messages m ON c.conversation_id = m.conversation_id
            ORDER BY c.updated_at DESC
        """
        cursor.execute(query)
        conversations = cursor.fetchall()
        cursor.close()
        conn.close()
    return conversations

def delete_conversation(conversation_id: str):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE conversation_id = %s", (conversation_id,))
        conn.commit()
        cursor.close()
        conn.close()

def get_messages(conversation_id: str) -> List[Dict]:
    messages = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE conversation_id = %s ORDER BY timestamp ASC",
            (conversation_id,)
        )
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
    return messages

def add_message(conversation_id: str, role: str, content: str):
    # Ensure conversation exists before adding message (Lazy Create)
    ensure_conversation_exists(conversation_id)
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Insert message
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
            (conversation_id, role, content)
        )
        # Update conversation timestamp
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = %s",
            (conversation_id,)
        )
        
        # If it's the first user message, update the title
        if role == 'user':
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = %s",
                (conversation_id,)
            )
            count = cursor.fetchone()[0]
            if count == 1:
                title = content[:50] + "..." if len(content) > 50 else content
                cursor.execute(
                    "UPDATE conversations SET title = %s WHERE conversation_id = %s",
                    (title, conversation_id)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
