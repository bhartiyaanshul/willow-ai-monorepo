# 🧠 WillowAI — AI Voice SDR

WillowAI is an open-source, real-time voice SDR (Sales Development Representative) built with Python and React. It acts as a voice-based agent to qualify leads, respond to queries, and hand off conversations to human sales teams when needed.

---

## 🎯 Features

- 🎤 Real-time speech-to-text and text-to-speech
- 🤖 Conversational AI agent using OpenRouter
- 🔄 Full-duplex conversation flow (WIP)
- 📋 Collects and summarizes lead information
- 💬 Text-based interface for testing and demos
- ⚡ Fast, low-latency interactions via REST/WebSocket
- 📝 Robust logging and transcript review for all interactions
- 🛡️ Graceful error handling and recovery in both backend and frontend
- 💾 Persistent chat and lead storage (localStorage)
- 🧑‍💻 Easy to extend and customize

---

## 🛠️ Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Frontend   | React.js                      |
| Backend    | FastAPI (Python 3.8+)         |
| STT        | Whisper (OpenAI), Vosk        |
| TTS        | Coqui / Piper / gTTS          |
| AI Engine  | OpenRouter (open-source LLMs) |
| Streaming  | WebSockets (Planned)          |

---

## 🏗️ Architecture Overview

**Backend (Python/FastAPI):**
- Handles all AI, speech, and lead logic.
- `/talk` endpoint: Accepts user messages, returns bot reply, audio, and lead data. Robust error handling and logs all interactions to `interaction.log`.
- `/lead` endpoint: Returns lead summary after conversation ends.
- `stt.py`, `tts.py`, `chatbot.py`: Each module logs transcripts for review and has robust error handling.
- All user and bot messages are logged for audit and debugging.

**Frontend (React):**
- Main chat UI (`App.jsx`) with robust error handling, retry, and transcript logging to `localStorage`.
- Leads dashboard (`Leads.jsx`) for reviewing and deleting saved leads, with error banners.
- All user and bot messages are logged to `localStorage` for recovery and review.
- UI gracefully handles backend interruptions and allows retry.

**Logging & Transcripts:**
- Backend logs all interactions to `interaction.log` and module-specific transcript logs.
- Frontend logs all chat messages to `localStorage` (`willow_transcript`).
- Leads are saved in `localStorage` (`willow_leads`).

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

# Download Vosk model (if using Vosk STT)
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 🖥️ Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Run development server
npm start
```

---

## 📝 Logging, Error Handling, and Transcript Review

- **Backend:**
  - All user and bot messages, as well as errors, are logged to `backend/interaction.log`.
  - Each module (`stt.py`, `tts.py`, `chatbot.py`) logs transcripts for review.
  - Backend endpoints return user-friendly error messages and handle interruptions gracefully.
- **Frontend:**
  - All chat messages are logged to `localStorage` (`willow_transcript`).
  - Leads are saved in `localStorage` (`willow_leads`).
  - User-friendly error banners are shown for backend or local errors, with retry options.
  - UI recovers from interruptions and allows users to retry failed actions.

---

## 🧩 Extending WillowAI

- Add new AI models or swap out TTS/STT engines by editing `backend/tts.py`, `backend/stt.py`, or `backend/chatbot.py`.
- Customize the frontend UI in `frontend/src/App.jsx` and `frontend/src/Leads.jsx`.
- Add new endpoints or business logic in `backend/main.py`.

---

## 🏁 Notes

- For production deployment, see [Render](https://render.com/), [Railway](https://railway.app/), or [Vercel](https://vercel.com/).
- For license or public deployment, please draft a `LICENSE` file.
- Contributions, bug reports, and feature requests are welcome!

---

## 📄 License

This project is open-source. See `LICENSE` for details (to be added).

---

For questions or contributions, open an issue or pull request!
