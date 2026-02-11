
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL")
model = os.getenv("LLM_MODEL")

print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

if not api_key:
    print("Error: OPENROUTER_API_KEY not found in environment.")
    exit(1)

try:
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        default_headers={
            "HTTP-Referer": "https://pdf-search.ai",
            "X-Title": "Adaptive RAG"
        }
    )
    
    print("Sending test message...")
    response = llm.invoke("Hello, are you working?")
    print(f"Response: {response.content}")
    print("SUCCESS: LLM connection working.")
    
except Exception as e:
    print(f"FAILURE: {e}")
