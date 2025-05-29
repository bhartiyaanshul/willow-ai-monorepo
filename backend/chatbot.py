from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def get_bot_response(prompt: str):
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "http://localhost:3000",  # Or your frontend URL
            "X-Title": "Willow AI SDR",  # Or your app/site name
        },
        model="openai/gpt-4o",
        max_tokens=5,  # Limit tokens to fit your credit limit
        messages=[
            {"role": "system", "content": "You are a sales representative. Reply in 1-2 words only."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content
