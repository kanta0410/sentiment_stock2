
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GEMINI_API_KEY")
print(f"API KEY: {api_key[:10]}...")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content("Hi, test message.")
    print(f"RESPONSE: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
