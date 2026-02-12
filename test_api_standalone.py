"""
API Layer Testing Script
Tests all FastAPI endpoints
Requires: FastAPI server running on localhost:8000
"""
import requests
import uuid
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_PREFIX = "[API TEST]"

def print_test(test_name):
    print(f"\n{TEST_PREFIX} Testing: {test_name}")
    print("-" * 60)

def print_success(message):
    print(f"[PASS] {message}")

def print_error(message):
    print(f"[FAIL] ERROR: {message}")

def check_server_running():
    """Test 0: Check if FastAPI server is running"""
    print_test("Server Connection")
    try:
        response = requests.get(f"{BASE_URL}/conversations", timeout=2)
        print_success(f"Server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to FastAPI server")
        print_error("Please start the server: uvicorn api:app --reload")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_get_conversations():
    """Test 1: GET /conversations"""
    print_test("GET /conversations")
    try:
        response = requests.get(f"{BASE_URL}/conversations")
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            conversations = response.json()
            print_success(f"Retrieved {len(conversations)} conversations")
            
            # Validate structure if there are any conversations
            if conversations:
                first = conversations[0]
                required_fields = ['conversation_id', 'title', 'created_at', 'updated_at']
                for field in required_fields:
                    if field in first:
                        print_success(f"Field '{field}' present")
                    else:
                        print_error(f"Field '{field}' missing")
                        return False
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_create_conversation():
    """Test 2: POST /conversations"""
    print_test("POST /conversations")
    try:
        response = requests.post(f"{BASE_URL}/conversations")
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            
            if 'conversation_id' in data:
                conv_id = data['conversation_id']
                print_success(f"Created conversation: {conv_id}")
                return conv_id
            else:
                print_error("Response missing conversation_id")
                return None
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return None

def test_get_messages(conversation_id):
    """Test 3: GET /conversations/{id}/messages"""
    print_test(f"GET /conversations/{conversation_id}/messages")
    try:
        response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            messages = response.json()
            print_success(f"Retrieved {len(messages)} messages")
            
            # Validate structure if there are messages
            if messages:
                first = messages[0]
                required_fields = ['role', 'content', 'timestamp']
                for field in required_fields:
                    if field in first:
                        print_success(f"Field '{field}' present")
                    else:
                        print_error(f"Field '{field}' missing")
                        return False
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_ask_endpoint(conversation_id):
    """Test 4: POST /ask"""
    print_test("POST /ask")
    try:
        question = "What is 2+2?"
        print(f"Sending question: {question}")
        
        response = requests.post(
            f"{BASE_URL}/ask",
            json={
                "conversation_id": conversation_id,
                "question": question
            },
            timeout=30  # Give it time for AI response
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            
            if 'answer' in data:
                answer = data['answer']
                print_success(f"Received answer: {answer[:100]}...")
                return True
            else:
                print_error("Response missing 'answer' field")
                return False
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timed out (AI taking too long?)")
        return False
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_ask_endpoint_validation():
    """Test 5: POST /ask with invalid data"""
    print_test("POST /ask - Validation")
    try:
        # Missing conversation_id
        response1 = requests.post(
            f"{BASE_URL}/ask",
            json={"question": "test"}
        )
        
        # Missing question
        response2 = requests.post(
            f"{BASE_URL}/ask",
            json={"conversation_id": "test-id"}
        )
        
        # Both missing
        response3 = requests.post(
            f"{BASE_URL}/ask",
            json={}
        )
        
        # Check that server properly validates
        if response1.status_code == 400:
            print_success("Properly rejected missing conversation_id")
        else:
            print_error(f"Should reject missing conversation_id, got: {response1.status_code}")
            return False
            
        if response2.status_code == 400:
            print_success("Properly rejected missing question")
        else:
            print_error(f"Should reject missing question, got: {response2.status_code}")
            return False
            
        if response3.status_code == 400:
            print_success("Properly rejected empty request")
        else:
            print_error(f"Should reject empty request, got: {response3.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Validation test failed: {e}")
        return False

def test_delete_conversation(conversation_id):
    """Test 6: DELETE /conversations/{id}"""
    print_test(f"DELETE /conversations/{conversation_id}")
    try:
        response = requests.delete(f"{BASE_URL}/conversations/{conversation_id}")
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            
            if data.get('status') == 'success':
                print_success("Conversation deleted successfully")
                
                # Verify it's gone
                get_response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
                if get_response.status_code == 200:
                    messages = get_response.json()
                    if len(messages) == 0:
                        print_success("Verified: conversation messages deleted")
                        return True
                    else:
                        print_error(f"Messages still exist after deletion: {len(messages)}")
                        return False
                else:
                    # This is also OK - the conversation doesn't exist
                    print_success("Verified: conversation no longer accessible")
                    return True
            else:
                print_error(f"Unexpected response: {data}")
                return False
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Delete request failed: {e}")
        return False

def test_full_conversation_flow():
    """Test 7: Full conversation flow"""
    print_test("Full Conversation Flow")
    try:
        # 1. Create conversation
        conv_id = str(uuid.uuid4())
        print_success(f"Using conversation ID: {conv_id}")
        
        # 2. Ask first question
        print("Asking first question...")
        response1 = requests.post(
            f"{BASE_URL}/ask",
            json={
                "conversation_id": conv_id,
                "question": "Hello, who are you?"
            },
            timeout=30
        )
        
        if response1.status_code != 200:
            msg = f"First question failed: {response1.status_code}\nResponse: {response1.text}"
            print_error(msg)
            try:
                with open('last_error.txt', 'w', encoding='utf-8') as f:
                    f.write(msg)
            except:
                pass
            return False
        print_success("First question answered")
        
        # 3. Ask follow-up question
        print("Asking follow-up question...")
        response2 = requests.post(
            f"{BASE_URL}/ask",
            json={
                "conversation_id": conv_id,
                "question": "What did I just ask you?"
            },
            timeout=30
        )
        
        if response2.status_code != 200:
            print_error(f"Follow-up question failed: {response2.status_code}")
            return False
        print_success("Follow-up question answered")
        
        # 4. Check messages
        messages_response = requests.get(f"{BASE_URL}/conversations/{conv_id}/messages")
        if messages_response.status_code == 200:
            messages = messages_response.json()
            # Should have 2 user messages + 2 assistant messages = 4 total
            if len(messages) == 4:
                print_success(f"Conversation history correct: {len(messages)} messages")
            else:
                msg = f"Expected 4 messages, got {len(messages)}"
                print_error(msg)
                try:
                    with open('last_error.txt', 'w', encoding='utf-8') as f:
                        f.write(msg)
                except:
                    pass
                return False
        
        # 5. Cleanup
        requests.delete(f"{BASE_URL}/conversations/{conv_id}")
        print_success("Test conversation cleaned up")
        
        return True
        
    except Exception as e:
        print_error(f"Full flow test failed: {e}")
        try:
            with open('last_error.txt', 'w', encoding='utf-8') as f:
                import traceback
                f.write(f"EXCEPTION: {str(e)}\n\n")
                traceback.print_exc(file=f)
        except:
            pass
        return False

def main():
    print("=" * 60)
    print("API LAYER TEST SUITE")
    print("=" * 60)
    
    # First check if server is running
    if not check_server_running():
        print("\nCannot proceed without FastAPI server")
        print("Start server with: uvicorn api:app --reload")
        return 1
    
    # Create test conversation for tests that need it
    print_test("Setup - Creating Test Conversation")
    test_conv_id = None
    response = requests.post(f"{BASE_URL}/conversations")
    if response.status_code == 200:
        test_conv_id = response.json()['conversation_id']
        print_success(f"Test conversation created: {test_conv_id}")
    
    tests = [
        (test_get_conversations, []),
        (test_create_conversation, []),
        (test_get_messages, [test_conv_id] if test_conv_id else []),
        (test_ask_endpoint_validation, []),
        (test_full_conversation_flow, []),
    ]
    
    # Note: We skip individual ask test to avoid AI API costs, covered by full flow
    
    results = []
    for test_func, args in tests:
        try:
            result = test_func(*args) if args else test_func()
            # Handle tests that return data instead of bool
            if result is None:
                results.append((test_func.__name__, False))
            elif isinstance(result, bool):
                results.append((test_func.__name__, result))
            else:
                # Test returned data (like conversation ID), count as success
                results.append((test_func.__name__, True))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((test_func.__name__, False))
    
    # Cleanup test conversation if it was created
    if test_conv_id:
        print_test("Cleanup - Deleting Test Conversation")
        requests.delete(f"{BASE_URL}/conversations/{test_conv_id}")
        print_success("Cleanup complete")
    
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
        print("\nAll API tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
