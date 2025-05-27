from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from stt import listen
from chatbot import get_bot_response
from tts import speak, text_to_speech

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

@app.post("/talk")
async def talk(request: Request):
    data = await request.json()
    user_text = data.get("message")

    bot_reply = get_bot_response(user_text)
    audio_path = text_to_speech(bot_reply)

    return FileResponse(audio_path, media_type="audio/wav", filename="reply.wav")