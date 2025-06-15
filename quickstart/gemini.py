import os
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()

from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)