from dotenv import load_dotenv
import os

# Load .env from the project root
load_dotenv()

# Print the key (masked for safety)
key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"✅ API key loaded successfully: {key[:7]}...{key[-4:]}")
else:
    print("❌ API key not found! Check .env or load path.")
