import openai
import os

# Use OpenRouter-compatible API
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = os.getenv("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")  # Store this in a .env file

# Add this header to your OpenRouter requests
openai.requestssession.RequestsSession.request_headers = {
    "HTTP-Referer": "http://localhost:3000",  # or your frontend domain
    "X-Title": "Willow AI SDR",
}

def get_bot_response(prompt: str):
    response = openai.ChatCompletion.create(
        model="mistralai/mistral-7b-instruct",  # you can change this to mixtral, zephyr, etc.
        messages=[
            {"role": "system", "content": "You are a helpful sales assistant AI."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message["content"]
