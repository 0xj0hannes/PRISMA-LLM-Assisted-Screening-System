import os
from google import genai
from src.config import load_config

def main():
    print("--- Gemini API Test Script ---")
    
    # Load configuration
    config = load_config()
    api_key = config.get("GEMINI_API_KEY")
    model_name = config.get("MODEL_NAME")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return

    # Configure the SDK
    client = genai.Client(api_key=api_key)
    
    print(f"\n1. Listing available models:")
    try:
        for m in client.models.list():
            print(f"   - Name: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

    print(f"2. Testing configured model: {model_name}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello and briefly introduce yourself."
        )
        print(f"\nResponse from {model_name}:")
        print(f"---")
        print(response.text)
        print(f"---")
    except Exception as e:
        print(f"Error testing completion: {e}")
        print("\nNote: If you get a 404, the model name might be incorrect for your API key's region or tier.")
        print("Check the 'Listing available models' section above for valid names.")

if __name__ == "__main__":
    main()
