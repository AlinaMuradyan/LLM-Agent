import os
import sys
from config import OPENAI_API_KEY
from openai import OpenAI

def verify_openai():
    print(f"Testing OpenAI API with key: {OPENAI_API_KEY[:10]}...")
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        print("Attempting to list models...")
        # Simple call to verify auth
        client.models.list()
        print("[PASS] Authentication successful")
        
        print("Attempting chat completion with gpt-4o-mini...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10
        )
        print(f"[PASS] Chat completion successful. Response: {response.choices[0].message.content}")
        
        print("Attempting embedding generation with text-embedding-3-small...")
        emb_response = client.embeddings.create(
            model="text-embedding-3-small",
            input="Test embedding"
        )
        print(f"[PASS] Embedding successful. Vector length: {len(emb_response.data[0].embedding)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] OpenAI API Error: {e}")
        return False

if __name__ == "__main__":
    if verify_openai():
        sys.exit(0)
    else:
        sys.exit(1)
