"""
Database Layer Testing Script
Tests all database operations without external dependencies
"""
import sys
import uuid
from datetime import datetime

# Test configuration
TEST_PREFIX = "[DB TEST]"

def print_test(test_name):
    print(f"\n{TEST_PREFIX} Testing: {test_name}")
    print("-" * 60)

def print_success(message):
    print(f"[PASS] {message}")

def print_error(message):
    print(f"[FAIL] ERROR: {message}")

def test_database_connection():
    """Test 1: Database connection"""
    print_test("Database Connection")
    try:
        import database
        conn = database.get_db_connection()
        if conn:
            print_success("Successfully connected to MySQL database")
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print_success(f"Connected to database: {db_name}")
            cursor.close()
            conn.close()
            return True
        else:
            print_error("Failed to connect to database")
            return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False

def test_schema_exists():
    """Test 2: Verify tables exist"""
    print_test("Database Schema")
    try:
        import database
        conn = database.get_db_connection()
        if not conn:
            print_error("No database connection")
            return False
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = ['conversations', 'messages']
        for table in required_tables:
            if table in tables:
                print_success(f"Table '{table}' exists")
            else:
                print_error(f"Table '{table}' missing")
                return False
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print_error(f"Schema check failed: {e}")
        return False

def test_conversation_creation():
    """Test 3: Create conversation"""
    print_test("Conversation Creation")
    try:
        import database
        
        # Create a test conversation
        test_title = f"Test Chat {datetime.now().strftime('%H:%M:%S')}"
        conv_id = database.create_conversation(test_title)
        print_success(f"Created conversation: {conv_id}")
        
        # Verify it exists
        conversations = database.list_conversations()
        # Note: list_conversations only returns conversations with messages
        # So we need to manually query
        conn = database.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversations WHERE conversation_id = %s", (conv_id,))
        result = cursor.fetchone()
        
        if result and result['title'] == test_title:
            print_success(f"Conversation verified with title: {test_title}")
        else:
            print_error("Conversation not found in database")
            return False
        
        cursor.close()
        conn.close()
        
        # Cleanup
        database.delete_conversation(conv_id)
        print_success("Test conversation cleaned up")
        return True
        
    except Exception as e:
        print_error(f"Conversation creation failed: {e}")
        return False

def test_message_storage():
    """Test 4: Message storage and retrieval"""
    print_test("Message Storage and Retrieval")
    try:
        import database
        
        # Create conversation
        conv_id = database.create_conversation("Message Test")
        print_success(f"Created test conversation: {conv_id}")
        
        # Add messages
        test_messages = [
            ("user", "What is Python?"),
            ("assistant", "Python is a programming language."),
            ("user", "Tell me more"),
            ("assistant", "Python is widely used for AI and web development.")
        ]
        
        for role, content in test_messages:
            database.add_message(conv_id, role, content)
        print_success(f"Added {len(test_messages)} messages")
        
        # Retrieve messages
        messages = database.get_messages(conv_id)
        
        if len(messages) == len(test_messages):
            print_success(f"Retrieved all {len(messages)} messages")
        else:
            print_error(f"Expected {len(test_messages)} messages, got {len(messages)}")
            return False
        
        # Verify order and content
        for i, msg in enumerate(messages):
            expected_role, expected_content = test_messages[i]
            if msg['role'] == expected_role and msg['content'] == expected_content:
                print_success(f"Message {i+1} correct: {msg['role'][:4]}...")
            else:
                print_error(f"Message {i+1} mismatch")
                return False
        
        # Cleanup
        database.delete_conversation(conv_id)
        print_success("Test data cleaned up")
        return True
        
    except Exception as e:
        print_error(f"Message storage test failed: {e}")
        return False

def test_lazy_conversation_creation():
    """Test 5: Lazy conversation creation (ensure_conversation_exists)"""
    print_test("Lazy Conversation Creation")
    try:
        import database
        
        # Generate a new ID
        conv_id = str(uuid.uuid4())
        print_success(f"Generated test ID: {conv_id}")
        
        # Add a message without explicitly creating conversation first
        database.add_message(conv_id, "user", "Test lazy creation")
        print_success("Added message (should auto-create conversation)")
        
        # Verify conversation was created
        conn = database.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversations WHERE conversation_id = %s", (conv_id,))
        result = cursor.fetchone()
        
        if result:
            print_success(f"Conversation auto-created with title: {result['title']}")
        else:
            print_error("Lazy creation failed - conversation not found")
            return False
        
        cursor.close()
        conn.close()
        
        # Cleanup
        database.delete_conversation(conv_id)
        print_success("Test data cleaned up")
        return True
        
    except Exception as e:
        print_error(f"Lazy creation test failed: {e}")
        return False

def test_conversation_listing_filter():
    """Test 6: Conversation listing (should only show non-empty)"""
    print_test("Conversation Listing Filter")
    try:
        import database
        
        # Create empty conversation
        empty_id = database.create_conversation("Empty Chat")
        print_success("Created empty conversation")
        
        # Create conversation with messages
        filled_id = database.create_conversation("Filled Chat")
        database.add_message(filled_id, "user", "Hello")
        database.add_message(filled_id, "assistant", "Hi there!")
        print_success("Created conversation with messages")
        
        # List conversations
        conversations = database.list_conversations()
        conv_ids = [c['conversation_id'] for c in conversations]
        
        # Empty should NOT appear, filled should appear
        if empty_id not in conv_ids and filled_id in conv_ids:
            print_success("Filter working: empty chat hidden, filled chat shown")
        else:
            print_error(f"Filter broken: empty={empty_id in conv_ids}, filled={filled_id in conv_ids}")
            # Cleanup and return
            database.delete_conversation(empty_id)
            database.delete_conversation(filled_id)
            return False
        
        # Cleanup
        database.delete_conversation(empty_id)
        database.delete_conversation(filled_id)
        print_success("Test data cleaned up")
        return True
        
    except Exception as e:
        print_error(f"Listing filter test failed: {e}")
        return False

def test_cascade_deletion():
    """Test 7: Cascade deletion (deleting conversation deletes messages)"""
    print_test("Cascade Deletion")
    try:
        import database
        
        # Create conversation with messages
        conv_id = database.create_conversation("Delete Test")
        database.add_message(conv_id, "user", "Message 1")
        database.add_message(conv_id, "assistant", "Response 1")
        print_success("Created conversation with 2 messages")
        
        # Verify messages exist
        messages = database.get_messages(conv_id)
        if len(messages) != 2:
            print_error(f"Expected 2 messages, found {len(messages)}")
            return False
        
        # Delete conversation
        database.delete_conversation(conv_id)
        print_success("Deleted conversation")
        
        # Verify messages are also deleted
        messages_after = database.get_messages(conv_id)
        if len(messages_after) == 0:
            print_success("Cascade delete working: messages also deleted")
        else:
            print_error(f"Cascade delete failed: {len(messages_after)} messages remain")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Cascade deletion test failed: {e}")
        return False

def test_title_auto_update():
    """Test 8: Title auto-update from first user message"""
    print_test("Title Auto-Update")
    try:
        import database
        
        # Create conversation with default title
        conv_id = database.create_conversation("New Chat")
        print_success("Created conversation with default title")
        
        # Add first user message
        first_message = "What is machine learning and how does it work in detail?"
        database.add_message(conv_id, "user", first_message)
        print_success("Added first user message")
        
        # Check if title was updated
        conn = database.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title FROM conversations WHERE conversation_id = %s", (conv_id,))
        result = cursor.fetchone()
        
        expected_title = first_message[:50] + "..." if len(first_message) > 50 else first_message
        if result and result['title'] == expected_title:
            print_success(f"Title auto-updated to: {result['title']}")
        else:
            print_error(f"Title not updated. Expected: {expected_title}, Got: {result['title'] if result else 'None'}")
            cursor.close()
            conn.close()
            database.delete_conversation(conv_id)
            return False
        
        cursor.close()
        conn.close()
        
        # Cleanup
        database.delete_conversation(conv_id)
        print_success("Test data cleaned up")
        return True
        
    except Exception as e:
        print_error(f"Title auto-update test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("DATABASE LAYER TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_database_connection,
        test_schema_exists,
        test_conversation_creation,
        test_message_storage,
        test_lazy_conversation_creation,
        test_conversation_listing_filter,
        test_cascade_deletion,
        test_title_auto_update,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll database tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
