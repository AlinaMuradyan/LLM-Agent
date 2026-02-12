"""
Model Layer Testing Script
Tests AI/ML components with optional OpenAI mocking
"""
import sys
import numpy as np
from unittest.mock import Mock, patch
import uuid

TEST_PREFIX = "[MODEL TEST]"
USE_REAL_OPENAI = False  # Set to True to test with real OpenAI API (costs money!)

def print_test(test_name):
    print(f"\n{TEST_PREFIX} Testing: {test_name}")
    print("-" * 60)

def print_success(message):
    print(f"[PASS] {message}")

def print_error(message):
    print(f"[FAIL] ERROR: {message}")

def test_imports():
    """Test 0: Import model module"""
    print_test("Module Imports")
    try:
        import model
        print_success("Successfully imported model module")
        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

def test_token_counting():
    """Test 1: Token counting utilities"""
    print_test("Token Counting")
    try:
        import model
        
        # Test simple text
        text1 = "Hello world"
        count1 = model.count_tokens(text1)
        print_success(f"'{text1}' = {count1} tokens")
        
        # Test longer text
        text2 = "This is a longer sentence with more words to test token counting."
        count2 = model.count_tokens(text2)
        print_success(f"Longer text = {count2} tokens")
        
        # Longer should have more tokens
        if count2 > count1:
            print_success("Token counting increases with text length")
        else:
            print_error("Token counting logic may be broken")
            return False
        
        # Test message list counting
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        msg_count = model.count_message_list_tokens(messages)
        print_success(f"Message list = {msg_count} tokens")
        
        return True
        
    except Exception as e:
        print_error(f"Token counting test failed: {e}")
        return False

def test_message_selection():
    """Test 2: Message selection within token budget"""
    print_test("Message Selection Within Budget")
    try:
        import model
        
        # Create a history with multiple messages
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
            {"role": "user", "content": "Third question"},
            {"role": "assistant", "content": "Third answer"},
        ]
        
        # Test with tight budget (should only get last few messages)
        selected = model.select_recent_messages_within_budget(history, max_tokens=50)
        print_success(f"Selected {len(selected)} messages within 50 token budget")
        
        # Test with generous budget (should get all)
        selected_all = model.select_recent_messages_within_budget(history, max_tokens=1000)
        if len(selected_all) == len(history):
            print_success(f"Selected all {len(selected_all)} messages with large budget")
        else:
            print_error(f"Should select all messages with large budget, got {len(selected_all)}/{len(history)}")
            return False
        
        # Verify more recent messages are prioritized
        if selected_all[-1] == history[-1]:
            print_success("Most recent message is preserved")
        else:
            print_error("Message order not preserved")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Message selection test failed: {e}")
        return False

def test_vector_store_operations():
    """Test 3: FAISS vector store operations"""
    print_test("Vector Store Operations")
    try:
        import model
        
        # Create a fresh vector store
        test_store = model.FaissQAVectorStore()
        
        # Check it's empty
        if test_store.is_empty():
            print_success("New vector store is empty")
        else:
            print_error("New vector store should be empty")
            return False
        
        # Create dummy embeddings
        dim = 1536  # Standard OpenAI embedding dimension
        emb1 = np.random.rand(dim).astype('float32')
        emb2 = np.random.rand(dim).astype('float32')
        emb3 = np.random.rand(dim).astype('float32')
        
        # Add Q&A pairs
        test_store.add("What is Python?", "Python is a programming language.", emb1)
        test_store.add("What is Java?", "Java is also a programming language.", emb2)
        test_store.add("What is C++?", "C++ is a systems programming language.", emb3)
        
        print_success("Added 3 Q&A pairs to vector store")
        
        # Check it's not empty
        if not test_store.is_empty():
            print_success("Vector store is no longer empty")
        else:
            print_error("Vector store should not be empty after adding items")
            return False
        
        # Search with a query
        query_emb = np.random.rand(dim).astype('float32')
        results = test_store.search(query_emb, top_k=2)
        
        if len(results) == 2:
            print_success(f"Search returned {len(results)} results")
            for i, (q, a) in enumerate(results):
                print_success(f"Result {i+1}: {q[:30]}...")
        else:
            print_error(f"Expected 2 results, got {len(results)}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Vector store test failed: {e}")
        return False

def test_small_talk_filtering():
    """Test 4: Small talk filtering heuristic"""
    print_test("Small Talk Filtering")
    try:
        import model
        
        # Test small talk (should NOT be stored)
        small_talk = [
            ("Hi", "Hello!"),
            ("Thanks", "You're welcome!"),
            ("Bye", "Goodbye!"),
            ("ok", "Great!"),
        ]
        
        for q, a in small_talk:
            should_store = model.should_store_in_vector_memory(q, a)
            if not should_store:
                print_success(f"Correctly filtered: '{q}'")
            else:
                print_error(f"Should filter small talk: '{q}'")
                return False
        
        # Test meaningful Q&A (should be stored)
        meaningful = [
            ("What is machine learning?", "Machine learning is a subset of AI that enables systems to learn from data."),
            ("How do neural networks work?", "Neural networks consist of interconnected layers of nodes that process information."),
        ]
        
        for q, a in meaningful:
            should_store = model.should_store_in_vector_memory(q, a)
            if should_store:
                print_success(f"Correctly keeping: '{q[:30]}...'")
            else:
                print_error(f"Should store meaningful Q&A: '{q}'")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Small talk filtering test failed: {e}")
        return False

def test_embedding_generation():
    """Test 5: Embedding generation (requires OpenAI or mock)"""
    print_test("Embedding Generation")
    try:
        import model
        
        if not USE_REAL_OPENAI:
            print("Using MOCKED OpenAI (set USE_REAL_OPENAI=True for real test)")
            
            # Mock the OpenAI client
            with patch.object(model.client.embeddings, 'create') as mock_create:
                # Create a mock response
                mock_embedding = np.random.rand(1536).tolist()
                mock_response = Mock()
                mock_response.data = [Mock()]
                mock_response.data[0].embedding = mock_embedding
                mock_create.return_value = mock_response
                
                # Test embedding generation
                text = "Test text for embedding"
                embedding = model.embed_text(text)
                
                print_success(f"Generated embedding shape: {embedding.shape}")
                
                if embedding.shape[0] == 1536:
                    print_success("Embedding dimension correct (1536)")
                else:
                    print_error(f"Unexpected embedding dimension: {embedding.shape[0]}")
                    return False
                
                print_success("Mocked embedding generation works")
        else:
            # Real OpenAI test
            print("Using REAL OpenAI API (this will cost money!)")
            text = "Test text for embedding"
            embedding = model.embed_text(text)
            
            print_success(f"Generated real embedding shape: {embedding.shape}")
            
            if embedding.shape[0] == 1536:
                print_success("Real embedding dimension correct (1536)")
            else:
                print_error(f"Unexpected embedding dimension: {embedding.shape[0]}")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Embedding generation test failed: {e}")
        return False

def test_build_messages_for_model():
    """Test 6: Message construction for model"""
    print_test("Message Construction for Model")
    try:
        import model
        import database
        
        # Create a test conversation
        conv_id = str(uuid.uuid4())
        database.add_message(conv_id, "user", "What is Python?")
        database.add_message(conv_id, "assistant", "Python is a programming language.")
        database.add_message(conv_id, "user", "Tell me more")
        
        print_success(f"Created test conversation: {conv_id}")
        
        # Mock vector store to avoid needing embeddings
        with patch.object(model, 'build_vector_memory_context', return_value=[]):
            messages = model.build_messages_for_model(conv_id, "What are its features?")
            
            print_success(f"Built message list with {len(messages)} messages")
            
            # Should have: system message + history (3 msgs) + current question
            # = 1 system + 3 history + 1 current = 5 total
            # (no vector context because we mocked it)
            if len(messages) >= 4:  # At least system + some history + question
                print_success(f"Message list contains {len(messages)} messages")
            else:
                print_error(f"Message list too short: {len(messages)}")
                database.delete_conversation(conv_id)
                return False
            
            # Check first message is system
            if messages[0]['role'] == 'system':
                print_success("First message is system instruction")
            else:
                print_error("First message should be system instruction")
                database.delete_conversation(conv_id)
                return False
            
            # Check last message is user question
            if messages[-1]['role'] == 'user' and messages[-1]['content'] == "What are its features?":
                print_success("Last message is current user question")
            else:
                print_error("Last message should be current user question")
                database.delete_conversation(conv_id)
                return False
        
        # Cleanup
        database.delete_conversation(conv_id)
        print_success("Test conversation cleaned up")
        
        return True
        
    except Exception as e:
        print_error(f"Message construction test failed: {e}")
        return False

def test_qa_within_budget():
    """Test 7: Q&A pair selection within budget"""
    print_test("Q&A Pair Selection Within Budget")
    try:
        import model
        
        qa_pairs = [
            ("Q1" * 100, "A1" * 100),  # Long pair
            ("Q2" * 100, "A2" * 100),  # Long pair
            ("Q3" * 50, "A3" * 50),    # Medium pair
            ("Q4", "A4"),               # Short pair
        ]
        
        # Test with tight budget
        selected = model.select_vector_qa_within_budget(qa_pairs, max_tokens=100)
        print_success(f"Selected {len(selected)} Q&A pairs within 100 token budget")
        
        if len(selected) < len(qa_pairs):
            print_success("Budget constraint is working (not all pairs selected)")
        
        # Test with generous budget
        selected_all = model.select_vector_qa_within_budget(qa_pairs, max_tokens=10000)
        if len(selected_all) == len(qa_pairs):
            print_success(f"Selected all {len(selected_all)} pairs with large budget")
        else:
            print_error(f"Should select all with large budget, got {len(selected_all)}/{len(qa_pairs)}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Q&A selection test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("MODEL LAYER TEST SUITE")
    print("=" * 60)
    
    if not USE_REAL_OPENAI:
        print("\nRunning with MOCKED OpenAI API")
        print("Set USE_REAL_OPENAI=True in the script for real API testing")
    else:
        print("\nRunning with REAL OpenAI API (this will cost money!)")
    
    tests = [
        test_imports,
        test_token_counting,
        test_message_selection,
        test_vector_store_operations,
        test_small_talk_filtering,
        test_embedding_generation,
        test_build_messages_for_model,
        test_qa_within_budget,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
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
        print("\nAll model tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
