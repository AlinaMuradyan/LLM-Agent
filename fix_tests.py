import os

files = [
    "test_telegram_standalone.py",
    "test_api_standalone.py",
    "test_model_standalone.py",
    "test_database_standalone.py",
    "debug_runner.py"
]

for filename in files:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace specific chars with ASCII equivalents
        replacements = {
            '\u2713': '[PASS]',
            '\u2717': '[FAIL]',
            '\u26a0': 'WARNING', # ⚠️
            '\u274c': '[FAIL]', # ❌
            '\u2705': '[PASS]', # ✅
            '\U0001f389': '',   # 🎉
            '\U0001f41b': 'BUG', # 🐛
            '\U0001f4cb': '',   # 📋
            '\U0001f44b': '',   # 👋
            '\u26a0\ufe0f': 'WARNING',
        }
        
        new_content = content
        for char, replacement in replacements.items():
            new_content = new_content.replace(char, replacement)
            
        # Also strip any other non-ascii just in case
        final_content = ""
        for char in new_content:
            if ord(char) < 128:
                final_content += char
            else:
                final_content += "?" # Replace unknown with ?
                
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        print(f"Cleaned {filename}")
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
