"""
Debug Runner - Interactive Test Suite Runner
Provides a menu-driven interface to run tests and debug issues
"""
import sys
import subprocess
import os
from pathlib import Path

WORKSPACE = Path(r"c:\Users\alina\Desktop\Training ML\QA chatbot")

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_menu():
    print("\n Test Menu:")
    print("  1. Test Database Layer")
    print("  2. Test API Layer (requires FastAPI running)")
    print("  3. Test Model Layer (uses mocked OpenAI)")
    print("  4. Test Telegram Bot")
    print("  5. Run ALL Tests")
    print("  6. Start FastAPI Server")
    print("  7. Start Streamlit Frontend")
    print("  8. Show Known Issues")
    print("  9. Fix Known Bugs")
    print("  0. Exit")
    print()

def run_test_script(script_name, description):
    """Run a test script and display results"""
    print_header(description)
    script_path = WORKSPACE / script_name
    
    if not script_path.exists():
        print(f"[FAIL] Test script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(WORKSPACE),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n[PASS] {description} PASSED")
            return True
        else:
            print(f"\n[FAIL] {description} FAILED (exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"[FAIL] Error running test: {e}")
        return False

def start_service(command, service_name):
    """Start a service (FastAPI or Streamlit)"""
    print_header(f"Starting {service_name}")
    print(f"Command: {command}")
    print(f"Working directory: {WORKSPACE}")
    print("\nWARNING?  This will open in a new window. Press Ctrl+C there to stop.")
    print("Press Enter to continue...")
    input()
    
    try:
        # Start in a new PowerShell window
        subprocess.Popen(
            ["powershell", "-NoExit", "-Command", f"cd '{WORKSPACE}'; {command}"],
            cwd=str(WORKSPACE)
        )
        print(f"[PASS] {service_name} started in new window")
    except Exception as e:
        print(f"[FAIL] Error starting {service_name}: {e}")

def show_known_issues():
    """Display known bugs and issues"""
    print_header("Known Issues")
    
    issues = [
        {
            "id": 1,
            "severity": "HIGH",
            "component": "telegram.py",
            "description": "Uses 'chat_id' instead of 'conversation_id'",
            "impact": "Telegram bot cannot communicate with API",
            "fix": "Change 'chat_id' to 'conversation_id' in API request"
        },
        {
            "id": 2,
            "severity": "MEDIUM",
            "component": "config.py",
            "description": "API keys hardcoded in config file",
            "impact": "Security risk if committed to version control",
            "fix": "Move to environment variables (.env file)"
        },
        {
            "id": 3,
            "severity": "LOW",
            "component": "model.py",
            "description": "Vector store is in-memory only",
            "impact": "Long-term memory lost on server restart",
            "fix": "Add persistence to disk using pickle or FAISS save/load"
        },
    ]
    
    for issue in issues:
        print(f"\nBUG Issue #{issue['id']} - {issue['severity']} PRIORITY")
        print(f"   Component: {issue['component']}")
        print(f"   Problem: {issue['description']}")
        print(f"   Impact: {issue['impact']}")
        print(f"   Fix: {issue['fix']}")

def fix_telegram_bug():
    """Fix the chat_id vs conversation_id bug in telegram.py"""
    print_header("Fixing Telegram Bot Bug")
    
    telegram_file = WORKSPACE / "telegram.py"
    
    try:
        with open(telegram_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if bug exists
        if '"chat_id": chat_id' in content:
            print("BUG Bug detected: Found 'chat_id' in API request")
            print("Applying fix...")
            
            # Fix the bug
            old_code = '"chat_id": chat_id'
            new_code = '"conversation_id": str(chat_id)'
            content = content.replace(old_code, new_code)
            
            # Write back
            with open(telegram_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("[PASS] Fixed! Changed 'chat_id' to 'conversation_id'")
            print("   Telegram bot should now work with the API")
            return True
        else:
            print("[PASS] Bug not found - may already be fixed")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error fixing bug: {e}")
        return False

def run_all_tests():
    """Run all test suites in sequence"""
    print_header("Running All Tests")
    
    tests = [
        ("test_database_standalone.py", "Database Layer Tests"),
        ("test_model_standalone.py", "Model Layer Tests"),
        ("test_telegram_standalone.py", "Telegram Bot Tests"),
    ]
    
    results = []
    for script, description in tests:
        result = run_test_script(script, description)
        results.append((description, result))
    
    # Note about API tests
    print("\nWARNING?  Skipping API tests (requires FastAPI server)")
    print("    To run API tests: Start server with option 6, then run option 2")
    
    # Summary
    print_header("Overall Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for description, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {description}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n All automated tests passed!")
    else:
        print(f"\n[FAIL] {total - passed} test suite(s) failed")

def main():
    print_header("QA Chatbot Debug Runner")
    print("\nThis tool helps you debug and test all components of the QA chatbot.")
    
    while True:
        print_menu()
        choice = input("Select option: ").strip()
        
        if choice == "1":
            run_test_script("test_database_standalone.py", "Database Layer Tests")
        
        elif choice == "2":
            print("\nWARNING?  Make sure FastAPI server is running first!")
            confirm = input("Is the server running? (y/n): ").strip().lower()
            if confirm == 'y':
                run_test_script("test_api_standalone.py", "API Layer Tests")
            else:
                print("Start server with option 6 first")
        
        elif choice == "3":
            run_test_script("test_model_standalone.py", "Model Layer Tests")
        
        elif choice == "4":
            run_test_script("test_telegram_standalone.py", "Telegram Bot Tests")
        
        elif choice == "5":
            run_all_tests()
        
        elif choice == "6":
            start_service("uvicorn api:app --reload", "FastAPI Server")
        
        elif choice == "7":
            start_service("streamlit run streamlit_app.py", "Streamlit Frontend")
        
        elif choice == "8":
            show_known_issues()
        
        elif choice == "9":
            fix_telegram_bug()
        
        elif choice == "0":
            print("\n Goodbye!")
            break
        
        else:
            print("[FAIL] Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Interrupted by user. Goodbye!")
        sys.exit(0)
