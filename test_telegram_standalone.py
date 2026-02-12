"""
Telegram Bot Testing Script
Tests the Telegram bot integration
NOTE: The current telegram.py has a bug - it sends "chat_id" but the API expects "conversation_id"
"""
import sys
from unittest.mock import Mock, patch, MagicMock

TEST_PREFIX = "[TELEGRAM TEST]"

def print_test(test_name):
    print(f"\n{TEST_PREFIX} Testing: {test_name}")
    print("-" * 60)

def print_success(message):
    print(f"[PASS] {message}")

def print_error(message):
    print(f"[FAIL] ERROR: {message}")

def print_warning(message):
    print(f"WARNING: {message}")

def test_imports():
    """Test 0: Import telegram module"""
    print_test("Module Imports")
    try:
        import telegram as tg_module
        print_success("Successfully imported telegram module")
        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

def test_bot_initialization():
    """Test 1: Bot initialization"""
    print_test("Bot Initialization")
    try:
        from config import TELEGRAM_TOKEN
        
        # Mock the TeleBot to avoid actual connection
        with patch('telebot.TeleBot') as MockBot:
            mock_bot_instance = Mock()
            MockBot.return_value = mock_bot_instance
            
            # Import will create the bot
            import importlib
            import telegram as tg_module
            importlib.reload(tg_module)
            
            print_success("Bot initialized with token")
            
            # Check token is configured
            if TELEGRAM_TOKEN:
                print_success(f"Token configured: {TELEGRAM_TOKEN[:10]}...")
            else:
                print_error("Telegram token not configured")
                return False
        
        return True

    except Exception as e:
        print_error(f"Bot initialization failed: {e}")
        return False

def test_start_command():
    """Test 2: /start command handler"""
    print_test("/start Command Handler")
    try:
        with patch('telebot.TeleBot') as MockBot, \
             patch('telegram.requests.post') as mock_post:
            
            mock_bot_instance = Mock()
            MockBot.return_value = mock_bot_instance
            
            # Reload to get mocked version
            import importlib
            import telegram as tg_module
            importlib.reload(tg_module)
            
            # Create mock message
            mock_message = Mock()
            mock_message.chat.id = 12345
            
            # Call start handler
            tg_module.start(mock_message)
            
            # Verify bot.send_message was called
            if mock_bot_instance.send_message.called:
                call_args = mock_bot_instance.send_message.call_args
                chat_id = call_args[0][0]
                message_text = call_args[0][1]
                
                if chat_id == 12345:
                    print_success(f"Sent to correct chat: {chat_id}")
                else:
                    print_error(f"Wrong chat ID: {chat_id}")
                    return False
                
                if "QA bot" in message_text or "Ask me" in message_text:
                    print_success(f"Welcome message sent: '{message_text}'")
                else:
                    print_warning(f"Unexpected welcome message: '{message_text}'")
                
                return True
            else:
                print_error("send_message was not called")
                return False
        
    except Exception as e:
        print_error(f"/start command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_handler():
    """Test 3: Message handling and API forwarding"""
    print_test("Message Handler")
    try:
        with patch('telebot.TeleBot') as MockBot, \
             patch('telegram.requests.post') as mock_post:
            
            mock_bot_instance = Mock()
            MockBot.return_value = mock_bot_instance
            
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = {"answer": "This is a test answer"}
            mock_post.return_value = mock_response
            
            # Reload module
            import importlib
            import telegram as tg_module
            importlib.reload(tg_module)
            
            # Create mock message
            mock_message = Mock()
            mock_message.chat.id = 12345
            mock_message.text = "What is Python?"
            
            # Call message handler
            tg_module.handle_message(mock_message)
            
            # Verify API was called
            if mock_post.called:
                print_success("API request was made")
                
                # Check API call details
                call_args = mock_post.call_args
                url = call_args[0][0]
                json_data = call_args[1]['json']
                
                if url == "http://localhost:8000/ask":
                    print_success(f"Correct API endpoint: {url}")
                else:
                    print_error(f"Wrong API endpoint: {url}")
                    return False
                
                # BUG DETECTION: The code sends "chat_id" but API expects "conversation_id"
                if 'chat_id' in json_data:
                    print_warning("BUG BUG FOUND: Code sends 'chat_id' but API expects 'conversation_id'!")
                    print_warning("   This will cause the API to reject the request")
                    if 'conversation_id' not in json_data:
                        print_error("   Missing 'conversation_id' in request")
                        return False
                
                if 'question' in json_data and json_data['question'] == "What is Python?":
                    print_success(f"Question forwarded: '{json_data['question']}'")
                else:
                    print_error("Question not properly forwarded")
                    return False
            else:
                print_error("API was not called")
                return False
            
            # Verify bot sent response
            if mock_bot_instance.send_message.called:
                print_success("Bot sent response to user")
            else:
                print_error("Bot did not send response")
                return False
            
            return True
        
    except Exception as e:
        print_error(f"Message handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test 4: Error handling when API fails"""
    print_test("Error Handling")
    try:
        with patch('telebot.TeleBot') as MockBot, \
             patch('telegram.requests.post') as mock_post:
            
            mock_bot_instance = Mock()
            MockBot.return_value = mock_bot_instance
            
            # Mock API failure
            mock_post.side_effect = Exception("Connection refused")
            
            # Reload module
            import importlib
            import telegram as tg_module
            importlib.reload(tg_module)
            
            # Create mock message
            mock_message = Mock()
            mock_message.chat.id = 12345
            mock_message.text = "Test question"
            
            # Call message handler
            tg_module.handle_message(mock_message)
            
            # Verify bot sent error message
            if mock_bot_instance.send_message.called:
                call_args = mock_bot_instance.send_message.call_args
                message_text = call_args[0][1]
                
                if "Error" in message_text or "error" in message_text:
                    print_success(f"Error message sent to user: '{message_text[:50]}...'")
                    return True
                else:
                    print_error(f"Expected error message, got: '{message_text}'")
                    return False
            else:
                print_error("Bot did not send error message")
                return False
        
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False

def test_api_parameter_fix_verification():
    """Test 5: Verify the chat_id vs conversation_id fix"""
    print_test("API Parameter Bug Fix Verification")
    try:
        # Check source code directly
        with open('telegram.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '"conversation_id": str(chat_id)' in content:
            print_success("Fix verified: Code uses 'conversation_id'")
            return True
        elif '"conversation_id": chat_id' in content:
             print_success("Fix verified: Code uses 'conversation_id'")
             return True
        else:
            print_error("Fix NOT found: Code still seems to use 'chat_id' or has other issue")
            return False
        
    except Exception as e:
        print_error(f"Fix verification failed: {e}")
        return False

def main():
    print("=" * 60)
    print("TELEGRAM BOT TEST SUITE")
    print("=" * 60)
    print("\nNote: These tests use mocked Telegram API to avoid")
    print("    requiring actual bot connection.")
    
    tests = [
        test_imports,
        test_bot_initialization,
        test_start_command,
        test_message_handler,
        test_error_handling,
        test_api_parameter_fix_verification,
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
    
    # Special note about the bug
    if not results[-1][1]:  # If bug detection test "failed" (found the bug)
        print("\nBUG BUG DETECTION:")
        print("telegram.py needs to be fixed to work with the API!")
    
    if passed == total - 1:  # All pass except known bug
        print("\nWARNING?  Tests pass but known bug exists - needs fixing")
        return 1
    elif passed == total:
        print("\n All Telegram tests passed!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
