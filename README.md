# 🧠 WillowAI — AI Voice SDR

WillowAI is an open-source, real-time voice SDR (Sales Development Representative) built with Python and React. It acts as a voice-based agent to qualify leads, respond to queries, and hand off conversations to human sales teams when needed.

---

## 🎯 Features

- 🎤 Real-time speech-to-text and text-to-speech.
- 🤖 Conversational AI agent using OpenRouter.
- 🔁 Supports full-duplex conversation flow (WIP).
- 📋 Collects and summarizes lead information.
- 💬 Text-based interface for testing and demos.
- ⚡ Fast, low-latency interactions via REST/WebSocket.

---

## 🛠️ Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Frontend   | React.js                      |
| Backend    | FastAPI (Python 3.8+)         |
| STT        | Whisper (OpenAI), Vosk        |
| TTS        | Coqui / Piper (configurable)  |
| AI Engine  | OpenRouter (open-source LLMs) |
| Streaming  | WebSockets (Planned)          |

---

## 📦 Setup Instructions

### ✅ Prerequisites

- Python >= 3.8 (we recommend 3.8.10)
- Node.js >= 16.x
- `ffmpeg` (required for audio processing)
- `pyenv` (recommended for managing Python versions)
- `yarn` or `npm`

---

### 🔧 Backend Setup

```bash
# Clone the repo
git clone https://github.com/your-username/willow-ai.git
cd willow-ai/backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Run development server
npm start

```


Let me know when you’re ready to draft the `LICENSE` file or prepare for public deployment (e.g., Render, Railway, Vercel).
