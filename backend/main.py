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
import httpx
import os
from dotenv import load_dotenv

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

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

async def get_gemini_reply(prompt):
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_API_URL, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            # Gemini returns: candidates[0].content.parts[0].text
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        # Log the error and return a fallback message
        logging.error(f"Gemini API error: {e}")
        return None

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

@app.post("/reset")
async def reset():
    conversation_state["step"] = 0
    conversation_state["lead"] = {}
    conversation_state["history"] = []
    return {"status": "reset"}

@app.post("/lead")
async def get_lead(request: Request):
    data = await request.json()
    user_text = (data.get("message") or "").strip()
    lead = conversation_state.get("lead", {})
    # If a message is provided, treat this as a lead finalization request
    if user_text:
        # Compose a summary prompt for Gemini
        conversation_str = "\n".join([
            ("User: " + h["text"]) if h["role"] == "user" else ("Jane: " + h["text"]) for h in conversation_state["history"]
        ])
        summary_prompt = f"""
Summarize this sales conversation in 5-6 sentences for a human sales agent. Include:
- The user's name, company, and role (if provided)
- The user's requirements and main problem
- Any objections or concerns
- Budget (if mentioned)
- Any other relevant details for handoff

Conversation:
{conversation_str}

Now, output a JSON object with the following fields: company, domain, problem, budget, summary, user_last_message, and a short summary for the agent. If any field is missing, set it to null. Example:
{{
  "company": ...,
  "domain": ...,
  "problem": ...,
  "budget": ...,
  "summary": ...,
  "user_last_message": ...,
  "agent_summary": ...
}}
"""
        gemini_json = await get_gemini_reply(summary_prompt)
        if not gemini_json:
            bot_reply = "Sorry, the AI backend is currently unavailable. Please try again later."
            return JSONResponse({
                "reply": bot_reply,
                "lead": None,
                "end": True
            })
        import json
        try:
            lead_summary = json.loads(gemini_json)
        except Exception:
            # fallback: just use summary as before
            lead_summary = {
                "summary": gemini_json,
                "conversation": conversation_state["history"][:],
                "user_last_message": user_text,
                "company": lead.get("company"),
                "domain": lead.get("domain"),
                "problem": lead.get("problem"),
                "budget": lead.get("budget"),
                "agent_summary": None
            }
        lead_summary["conversation"] = conversation_state["history"][:]
        conversation_state["lead"] = lead_summary
        bot_reply = "Thank you for chatting with Willow AI! I've summarized your requirements for our team. Have a great day!"
        conversation_state["history"].append({"role": "bot", "text": bot_reply})
        lead_summary["conversation"] = conversation_state["history"][:]
        summary_filename = f"lead_summary_{random.randint(1000,9999)}.txt"
        summary_path = _os.path.join(audio_dir, summary_filename)
        with open(summary_path, "w") as f:
            f.write(lead_summary.get("summary", ""))
        return JSONResponse({
            "reply": bot_reply,
            "summary_file": f"/audio/{summary_filename}",
            "showImage": False,
            "lead": lead_summary,
            "end": True,
            "youtube_url": None
        })
    # Otherwise, just return the current lead
    return JSONResponse({"lead": lead})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
SYSTEM_PROMPT = '''
Role & Objective:
You are Jane, an AI SDR for Willow AI, an AI-powered sales agent designed to engage, qualify, and convert inbound leads for B2B companies. Your job is to:

Engage prospects in a natural, conversational manner.
Qualify leads based on their business needs, sales process, and budget.
Explain Willow AI’s value concisely and in a way that resonates with their persona.
Handle objections effectively by reinforcing benefits and addressing concerns.
Book a meeting with an AE if the lead is a good fit.

Only refer to the knowledge base for information related to the product. For anything about what your role is and how you need to talk to the prospect, refer to this prompt.

1️⃣ Ask the prospect their name, company and their current role.
Focus on these personas during qualification:
✅ VP of Sales / Head of Sales – Struggles with inbound lead conversion and SDR efficiency.
✅ Sales Ops / RevOps Managers – Wants automation and better CRM integration.
✅ Marketing Leaders (CMO, Demand Gen, Growth Marketers, Product Marketing Managers (PMM)) – Needs better website lead conversion.
✅ Founders of PLG (Product-Led Growth) Companies – Wants self-serve sales acceleration.

2️⃣ Qualification Questions (Only Ask What’s Relevant to Their Role)
Before pitching, qualify them using relevant questions:

📌 General Business Fit
“How does your company currently handle inbound leads from your website?”
“Do you have SDRs qualifying leads, or do AEs handle them directly?”
“How do you decide whether a lead should talk to sales?”
📌 Pain Points & Need for Willow AI
“What’s your biggest challenge in converting website visitors into booked meetings?”
“Are you facing drop-offs because prospects don’t want to fill out a demo form?”
“How long does it typically take for a prospect to get a response after requesting a demo?”
📌 Current Tools & Interest in AI Automation
“Are you currently using tools like Drift, Intercom, or any other chatbot to engage visitors?”
“Do you have any AI automation in your sales funnel today?”
📌 Buying Readiness & Budget
“Are you actively looking for solutions to improve inbound lead conversion?”
“Do you have a budget allocated for AI or sales automation tools this quarter?”
3️⃣ Explaining Willow AI’s Value (Keep It Clear & Benefit-Driven)
Once the prospect shares challenges, position Willow AI accordingly:

🟢 How to Use This Context in a Conversation
Example 1: Prospect Asks How It Works
💬 Prospect: “So how does Willow AI actually work?”
🤖 AI Response: “Great question! Willow AI is like an SDR that instantly engages your inbound visitors, qualifies them, and either books a sales call or provides a demo—all in real-time. It integrates with your CRM so your team gets full visibility into every interaction. Are you looking to improve inbound lead conversion or streamline your SDR team’s workload?”

Example 2: Prospect Is Unsure About AI Handling Sales Calls
💬 Prospect: “I’m not sure if AI can actually replace a human SDR in handling our inbound leads.”
🤖 AI Response: “That’s a fair concern! Willow AI isn’t meant to replace SDRs but rather enhance their efficiency. Instead of SDRs spending hours on repetitive qualification, Willow AI engages leads instantly, handles common objections, and only passes qualified leads to your sales team—so they can focus on closing instead of filtering leads. Would that help your team?”

Example 3: Prospect Says They Already Have a Chatbot
💬 Prospect: “We already use a chatbot for lead capture.”
🤖 AI Response: “That’s great! Unlike traditional chatbots that just collect emails, Willow AI talks to leads, answers questions, qualifies them, and schedules meetings—just like a real SDR. Most chatbots still require human follow-up, while Willow AI drives real conversions instantly. Would you like to see a comparison of how we differ from your current solution?”

4️⃣ Handling Common Objections
📌 “We already use a chatbot like Drift/Intercom.”
👉 “That’s great! Unlike traditional chatbots, Willow AI doesn’t just collect emails—it actually talks to leads, qualifies them like an SDR, and schedules meetings automatically. Have you seen gaps in your current chatbot where leads still fall through?”

📌 “We prefer human SDRs for qualification.”
👉 “Willow AI isn’t replacing SDRs—it’s making them more efficient. Instead of spending time on repetitive qualification, your reps can focus on closing high-intent leads.”

📌 “Our leads need a personal touch, AI won’t work.”
👉 “That’s exactly why we designed Willow AI to sound human-like and handle objections dynamically. It’s trained on sales conversations, so it engages naturally, just like your best SDR would.”

📌 “What if AI makes mistakes in qualification?”
👉 “You define the qualification criteria, and Willow AI follows those rules. It can even flag leads for manual review if they need further evaluation.”

📌 “This sounds interesting, but we don’t have budget.”
👉 “I understand! Many of our customers see a fast ROI because Willow AI increases inbound conversion rates and reduces SDR workload. Would it make sense to explore a pilot program to see the impact firsthand?”

5️⃣ Closing the Conversation
1. Booking a Meeting
If the lead is qualified, move toward scheduling:

"Sounds like Willow AI could be a great fit for your team. I’d love to set up a quick demo with our sales expert to walk you through how companies like yours are using it. Does [Date/Time] work for you?"

🔹 If they agree: Book the meeting & confirm.
🔹 If they need more info: Offer a follow-up email with case studies or additional details.

Do not let a qualified lead get off the call without a clear next step. Push them to scheduling a follow-up call with a Human Account Executive who can address their more complex and custom requirements and give a customized demo.
For example: If they say "That's all I needed, we can end the call now.", push for them to have a next call "Great, I can schedule a customized demo call with John, our account executive. Would you mind giving me your availability?"

2. If the lead's requirements do not match what Willow AI offers, feel free to close the call without scheduling a follow-up conversation.

Final Notes for the Voice Agent:
Prioritize conversation over scripted response.
Only pitch after qualifying the prospect’s needs.
If the lead isn’t a fit, politely end the call but tag them for potential future engagement.
Prioritize scheduling a call with an AE if the lead shows strong interest.
'''

KNOWLEDGE_BASE = '''
Willow AI Knowledge Base

Section 1: What is Willow AI?

Overview:Willow AI is an AI-powered sales agent designed to engage, qualify, and convert inbound leads in real time. Instead of waiting for human sales reps, website visitors can interact with Willow AI to:✅ Ask product-related questions & get instant answers✅ See personalized demos based on their needs✅ Handle objections dynamically like a real SDR✅ Qualify or disqualify leads based on pre-set criteria✅ Sync lead information into CRM & book meetings automatically

Additional features and use cases:

Can act as a way to let the users know the information they're looking for just by talking to the AI on a website instead of manually reading it, navigating to other pages to look at more features etc.

Can be used in comparison pages where AI can understand the prospect's use case and pitch why a product would be a good fit for them.

Can be used in the pricing page to help people with the right plan for them (can even provide a discount)

Can be used in navigation menu where there are lots of options and features that might overwhelm the users.

Can be used as a notetaker for account executive's calls while also doubling down as an AI assistant that can unmute and help the AE out if they need any help with the talk track, knowledge about the product etc., all via voice like a normal human assistant. If the AI assistant doesn't know about something on the product it can ping on the product channel on slack and ask a question while the call is going on. If someone answers, it can bring it back to the call, unmute and give the answer to the account executive.

How It Works:

A visitor arrives on the company’s website and clicks "Get Instant Demo" (or any CTA).

Willow AI starts a human-like conversation to understand their intent.

Based on responses, Willow AI qualifies the lead or guides them through a product demo.

If the lead is a fit, Willow AI books a call with sales or assists in a self-serve purchase.

All conversation data is synced to CRM for seamless handoff.

What are certain unique selling points about Willow AI?

Superior quality of answers compared to other conversational AI tools. Specially trained and tweaked to make AI sound human and at the same time have clear context and higher quality answers

Train the AI like how you onboard a human SDR - by getting on onboarding calls. AI will ask questions so that it has the most context, you can answer via voice or feed URLs and documents via chat and AI will learn from it

Focus on meetings - Willow AI is the only AI SDR that focuses on simulating a meeting.

Demo on Demand - Willow AI is the only AI SDR that asks questions, understands the prospect's needs and gives an instant demo by sharing pre defined clips

Seamless handoff - Willow AI increases visibility within the organization by summarizing the call into different sales methodologies like MEDDIC, BANT etc. It also infers deal health, records pain points, objections, use cases of the user so the Account Executive that takes over the deal from the AI can get quick context without having to go through the entire recording.

Section 2: How Willow AI Helps Different Company Sizes

🔹 For Startups & Small Businesses

Automates lead capture & qualification without hiring an SDR team.

Ensures every inbound lead is engaged instantly, even outside business hours.

Affordable alternative to hiring full-time SDRs.

🔹 For Mid-Market Companies

Reduces SDR workload so teams focus on closing deals, not qualification.

Improves website-to-meeting conversion rates, preventing lead drop-offs.

Provides data-backed insights on why leads convert or drop off.

🔹 For Enterprise Companies

Supports complex qualification workflows and integrates into existing sales pipelines.

Ensures compliance & data security with enterprise-grade AI governance.

Scales lead engagement across multiple regions & languages without increasing SDR headcount.

Section 3: Addressing Common Objections

1️⃣ Would enterprise customers be willing to speak to an AI agent?✅ Yes! Many enterprises are already adopting AI-powered sales tools like Gong, Drift AI, and Intercom AI.✅ Data shows buyers prefer self-serve interactions before talking to sales. Forrester Research found 60%+ of B2B buyers prefer self-service over speaking to a rep.✅ Willow AI ensures human-like conversations so buyers don’t feel like they are talking to a chatbot.

If enterprise users engage with chatbots, they are almost certain to engage with voice based AI agents too.

2️⃣ Can Willow AI progressively understand information without asking for email/name upfront?✅ Yes! Willow AI follows a progressive profiling approach, meaning it:

Starts the conversation naturally without asking for details upfront.

Learns context from previous responses to personalize the interaction.

Only asks for contact details when necessary (e.g., before booking a meeting).

3️⃣ Is there any validation in the market that people are ready to talk to AI?✅ Yes, strong validation!

AI-driven chatbots like Drift and Intercom AI already engage leads on thousands of websites.

Gartner predicts that by 2026, 85% of B2B interactions will be AI-powered.

Willow AI goes beyond basic chatbots by handling objections, showing demos, and driving conversions.

There is GEO (Generative Engine Optimization) that's helping a lot of businesses. If people are searching through AI to know about products, they are certain to use voice based AI in websites to know about the product instead of reading and going through the website manually.

4️⃣ What if AI makes mistakes in qualification?✅ Willow AI follows a strict qualification framework (e.g., BANT, MEDDIC) to ensure accuracy.✅ Leads that don’t clearly qualify are flagged for human review, reducing the risk of errors.✅ Willow AI continuously learns from previous interactions, improving its accuracy over time.

5️⃣ Will customers trust AI to handle objections?✅ AI objection handling is already a proven market trend (used by Gong, Drift AI, and others).✅ Willow AI trains on real sales conversations to mimic human SDR responses.✅ AI uses data-driven insights to overcome common objections logically.

6️⃣ How does Willow AI compare to a traditional chatbot?❌ Chatbots only collect emails.✅ Willow AI actually qualifies leads, books meetings, and handles objections.

❌ Chatbots provide scripted responses.✅ Willow AI generates dynamic, natural conversations based on the lead’s responses.

❌ Chatbots don’t provide product demos.✅ Willow AI shares interactive demos and walkthroughs instantly.

7️⃣ Can Willow AI integrate with our CRM?✅ Yes! Willow AI integrates with Salesforce, HubSpot, Zoho CRM, Pipedrive, and more.✅ Auto-syncs conversation data, qualification details, and meeting schedules into the CRM.

8️⃣ Can Willow AI handle multiple languages?✅ Yes! Supports multilingual conversations for global audiences.✅ AI can adapt to different regional selling styles & preferences.

9️⃣ What happens if AI doesn’t know the answer?✅ Willow AI routes the conversation to a human agent if needed.✅ It can also capture the question and follow up via email once a rep provides the answer.
'''

# Store conversation history in memory (for demo, just last 10 turns)
if "history" not in conversation_state:
    conversation_state["history"] = []

# Update speak/text_to_speech usage to save files in audio_dir
from tts import text_to_speech as _orig_text_to_speech

audio_dir = _os.path.join(_os.path.abspath(_os.path.dirname(__file__)), "audio")
_os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

def speak(text):
    # Increase speed by setting a higher playback rate (e.g., 1.2x)
    filename = _orig_text_to_speech(text, speed=1.2)  # Pass speed param if supported
    base = _os.path.basename(filename)
    target = _os.path.join(audio_dir, base)
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

@app.post("/talk")
async def talk(request: Request):
    data = await request.json()
    user_text = (data.get("message") or "").strip()
    step = conversation_state["step"]
    lead = conversation_state["lead"]

    if user_text:
        conversation_state["history"].append({"role": "user", "text": user_text})
    # Only keep last 10 turns
    conversation_state["history"] = conversation_state["history"][-10:]

    # Detect end-of-conversation intent
    end_keywords = [
        "bye", "ok bye", "thank you", "thankyou", "thanks", "see you", "goodbye", "talk later", "end chat", "end conversation", "that's all", "done", "finish", "no more", "that's it"
    ]
    user_text_lower = user_text.lower()
    if any(kw in user_text_lower for kw in end_keywords):
        # Compose a summary prompt for Gemini
        conversation_str = "\n".join([
            ("User: " + h["text"]) if h["role"] == "user" else ("Jane: " + h["text"]) for h in conversation_state["history"]
        ])
        summary_prompt = f"""
Summarize this sales conversation in 5-6 sentences for a human sales agent. Include:
- The user's name, company, and role (if provided)
- The user's requirements and main problem
- Any objections or concerns
- Budget (if mentioned)
- Any other relevant details for handoff

Conversation:
{conversation_str}

Now, output a JSON object with the following fields: company, domain, problem, budget, summary, user_last_message, and a short summary for the agent. If any field is missing, set it to null. Example:
{{
  "company": ...,
  "domain": ...,
  "problem": ...,
  "budget": ...,
  "summary": ...,
  "user_last_message": ...,
  "agent_summary": ...
}}
"""
        gemini_json = await get_gemini_reply(summary_prompt)
        if not gemini_json:
            bot_reply = "Sorry, the AI backend is currently unavailable. Please try again later."
            return JSONResponse({
                "reply": bot_reply,
                "lead": None,
                "end": True
            })
        import json
        try:
            lead_summary = json.loads(gemini_json)
        except Exception:
            # fallback: just use summary as before
            lead_summary = {
                "summary": gemini_json,
                "conversation": conversation_state["history"][:],
                "user_last_message": user_text,
                "company": lead.get("company"),
                "domain": lead.get("domain"),
                "problem": lead.get("problem"),
                "budget": lead.get("budget"),
                "agent_summary": None
            }
        lead_summary["conversation"] = conversation_state["history"][:]
        conversation_state["lead"] = lead_summary
        bot_reply = "Thank you for chatting with Willow AI! I've summarized your requirements for our team. Have a great day!"
        conversation_state["history"].append({"role": "bot", "text": bot_reply})
        lead_summary["conversation"] = conversation_state["history"][:]
        summary_filename = f"lead_summary_{random.randint(1000,9999)}.txt"
        summary_path = _os.path.join(audio_dir, summary_filename)
        with open(summary_path, "w") as f:
            f.write(lead_summary.get("summary", ""))
        return JSONResponse({
            "reply": bot_reply,
            "summary_file": f"/audio/{summary_filename}",
            "showImage": False,
            "lead": lead_summary,
            "end": True,
            "youtube_url": None
        })

    # Build conversation string for Gemini
    conversation_str = "\n".join([
        ("User: " + h["text"]) if h["role"] == "user" else ("Jane: " + h["text"]) for h in conversation_state["history"]
    ])

    # If user asks for a video/demo, always provide a sample video link
    import re
    video_keywords = ["video", "demo", "show", "see", "sample"]
    if any(kw in user_text.lower() for kw in video_keywords):
        # Use a real or placeholder YouTube video link
        sample_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with your real demo if available
        bot_reply = (
            f"Absolutely! Here's a quick demo video of Willow AI in action: {sample_video_url}\n"
            "This video will show you how Willow AI engages leads, qualifies them, and books meetings in real time. Let me know if you have any questions after watching!"
        )
        conversation_state["history"].append({"role": "bot", "text": bot_reply})
        audio_path = speak(bot_reply)
        return JSONResponse({
            "reply": bot_reply,
            "audio_url": f"/audio/{audio_path}" if audio_path else None,
            "showImage": False,
            "lead": lead,
            "end": False,
            "youtube_url": sample_video_url
        })

    # Initial prompt for first message
    if len(conversation_state["history"]) == 1:
        prompt = f"""{SYSTEM_PROMPT}\n\nKnowledge Base:\n{KNOWLEDGE_BASE}\n\nConversation so far:\n{conversation_str}\nCurrent step: {step}\nCollected lead info: {lead}\nYour reply (be concise, human, and impactful):\n"""
    else:
        prompt = f"""{SYSTEM_PROMPT}\n\nKnowledge Base:\n{KNOWLEDGE_BASE}\n\nConversation so far:\n{conversation_str}\nCurrent step: {step}\nCollected lead info: {lead}\nYour reply (be concise, human, and impactful):\n"""

    bot_reply = await get_gemini_reply(prompt)
    if not bot_reply:
        bot_reply = "Sorry, the AI backend is currently unavailable. Please try again later."
        conversation_state["history"].append({"role": "bot", "text": bot_reply})
        return JSONResponse({
            "reply": bot_reply,
            "audio_url": None,
            "showImage": False,
            "lead": lead,
            "end": False,
            "youtube_url": None
        })

    conversation_state["history"].append({"role": "bot", "text": bot_reply})

    # Detect YouTube video link in bot_reply (simple regex for demo)
    youtube_url = None
    yt_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[\w\-?&=%.]+)', bot_reply)
    if yt_match:
        youtube_url = yt_match.group(1)

    # Use TTS for the reply
    audio_path = speak(bot_reply)
    return JSONResponse({
        "reply": bot_reply,
        "audio_url": f"/audio/{audio_path}" if audio_path else None,
        "showImage": False,
        "lead": lead,
        "end": False,
        "youtube_url": youtube_url
    })