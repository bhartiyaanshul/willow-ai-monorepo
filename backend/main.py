from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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