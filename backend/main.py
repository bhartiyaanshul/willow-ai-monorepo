from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Response
from fastapi.staticfiles import StaticFiles
import uvicorn
from tts import speak, text_to_speech
import os as _os
import random
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server (Vite and CRA)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory state for demo (use a database or session in production)
conversation_state = {
    "step": 0,
    "lead": {}
}

qualifying_questions = [
    ("company", "What is your company name?"),
    ("domain", "What is your company domain?"),
    ("problem", "What problem are you looking to solve?"),
    ("budget", "What is your budget for this project?")
]

@app.get("/")
async def root():
    return {"message": "Backend up"}

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🎤 Connected to frontend")

    while True:
        try:
            data = await websocket.receive_bytes()
            print("🔊 Received audio data:", len(data))

            # (STT → Bot Logic → TTS → send audio back)
            await websocket.send_text("Hello from backend!")  # TEMP
        except Exception as e:
            print("❌ Error:", e)
            break

@app.options("/talk")
async def options_talk():
    return {}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
@app.post("/talk")
async def talk(request: Request):
    data = await request.json()
    user_text = (data.get("message") or "").strip()
    step = conversation_state["step"]
    lead = conversation_state["lead"]

    def speak_and_respond(text, show_image=False, end=False):
        audio_path = speak(text)
        if not audio_path:
            logging.error(f"No audio generated for text: {text}")
            return JSONResponse({
                "reply": text,
                "audio_url": None,
                "showImage": show_image,
                "lead": lead,
                "end": end
            })
        return JSONResponse({
            "reply": text,
            "audio_url": f"/audio/{audio_path}",
            "showImage": show_image,
            "lead": lead,
            "end": end
        })

    # Step 0: Greet user and ask first qualifying question together
    if step == 0:
        greetings = [
            "Hi there! 👋 I'm Willow, your sales assistant. Thanks for reaching out!",
            "Hello and welcome! I'm Willow. Excited to learn about your business and see how we can help.",
            "Hey! Willow here. I’m here to make your experience smooth and valuable."
        ]
        greeting = random.choice(greetings)
        _, first_question = qualifying_questions[0]
        reply = f"{greeting} {first_question}"
        conversation_state["step"] = 1
        return speak_and_respond(reply)

    # Steps 1-4: Qualifying questions with empathy and context
    if 1 <= step <= 4:
        # Save previous answer if any
        if user_text:
            key, _ = qualifying_questions[step - 1]
            lead[key] = user_text

        # Personalized follow-up if answer is too short
        if user_text and len(user_text.split()) < 2:
            follow_ups = [
                "Could you tell me a bit more?",
                "I'd love a little more detail if you don't mind.",
                "Feel free to elaborate, it helps us serve you better!"
            ]
            reply = random.choice(follow_ups)
            return speak_and_respond(reply)

        if step == 4:
            # After last qualifying question, confirm info and invite questions
            summary = (
                f"Thank you for sharing these details! Just to confirm, your company is '{lead.get('company', 'N/A')}', "
                f"in the '{lead.get('domain', 'N/A')}' space, facing '{lead.get('problem', 'N/A')}', "
                f"with a budget around '{lead.get('budget', 'N/A')}'."
                " Did I get that right? 😊\n"
                "Feel free to ask me anything about our products, or let me know if you'd like a quick demo!"
            )
            conversation_state["step"] = 5
            return speak_and_respond(summary, show_image=True)

        else:
            # Ask next qualifying question, with natural phrasing
            _, next_question = qualifying_questions[conversation_state["step"]]
            question_variants = [
                f"{next_question}",
                f"Could you please tell me, {next_question.lower()}",
                f"May I know, {next_question.lower()}",
                f"I'd love to know, {next_question.lower()}",
            ]
            reply = random.choice(question_variants)
            conversation_state["step"] += 1
            return speak_and_respond(reply)

    # Step 5+: Handle product/service questions, show media, or end call
    if step >= 5:
        lower_text = user_text.lower()

        # Handle polite endings / wrap-up
        if any(word in lower_text for word in ["bye", "thank you", "thanks", "end", "no more"]):
            lead_summary = (
                f"Lead details:\n"
                f"- Company: {lead.get('company', 'N/A')}\n"
                f"- Domain: {lead.get('domain', 'N/A')}\n"
                f"- Problem: {lead.get('problem', 'N/A')}\n"
                f"- Budget: {lead.get('budget', 'N/A')}"
            )
            conversation_state["step"] = 0
            conversation_state["lead"] = {}

            closing_phrases = [
                "Thank you so much for your time! One of our experts will reach out soon to help you further. Have a wonderful day!",
                "It was a pleasure chatting with you! We'll be in touch soon. Take care!",
                "Thanks for sharing your needs. Our team will follow up to make sure you get the best solution."
            ]
            reply = random.choice(closing_phrases)
            return speak_and_respond(reply, end=True)

        # Detect product/demo/media request
        media_keywords = ["demo", "show me", "video", "image", "product", "feature"]
        if any(kw in lower_text for kw in media_keywords):
            media_reply = (
                "Absolutely! Here’s a quick demo video of our flagship product, designed to solve challenges just like yours. "
                "Let me know if you’d like a deeper dive or have specific questions!"
            )
            return speak_and_respond(media_reply, show_image=True)

        # Handle common FAQ-type questions (with more human touch)
        faq_keywords = {
            "pricing": "Great question! Our pricing is flexible and tailored to your needs. Would you like a custom quote or a general overview?",
            "support": "We pride ourselves on 24/7 support and dedicated account managers. Is there a particular support feature you’re interested in?",
            "integration": "Our platform integrates seamlessly with most industry-standard tools. Are there any specific platforms you use?",
            "features": "We offer automation, real-time analytics, and AI-powered recommendations. Is there a feature you’re most interested in?"
        }
        for k, v in faq_keywords.items():
            if k in lower_text:
                return speak_and_respond(v)

        # If no specific keywords matched, provide a generic helpful response
        generic_replies = [
            "That’s a great question! Could you share a bit more about what you’d like to know?",
            "I’m here to help! Feel free to ask about our services, pricing, or request a demo anytime.",
            "Could you tell me more about what you’re interested in? I’ll do my best to guide you."
        ]
        reply = random.choice(generic_replies)
        return speak_and_respond(reply)

    # Fallback generic response
    reply = "I'm here to assist you! How can I help today?"
    return speak_and_respond(reply)

# Serve audio files from backend/audio directory
audio_dir = _os.path.join(_os.path.abspath(_os.path.dirname(__file__)), "audio")
_os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Update speak/text_to_speech usage to save files in audio_dir
from tts import text_to_speech as _orig_text_to_speech

def speak(text):
    filename = _orig_text_to_speech(text)
    base = _os.path.basename(filename)
    target = _os.path.join(audio_dir, base)
    # Only move if the file exists and is not already in audio_dir
    if filename != target:
        try:
            _os.replace(filename, target)
            logging.info(f"Moved TTS file to audio_dir: {target}")
        except FileNotFoundError:
            logging.error(f"TTS file not found: {filename}")
            return None
    else:
        logging.info(f"TTS file already in audio_dir: {target}")
    return base