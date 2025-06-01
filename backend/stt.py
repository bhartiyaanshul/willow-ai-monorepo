# backend/stt.py
import queue
import sounddevice as sd
import vosk
import sys
import json
from datetime import datetime

q = queue.Queue()

model = vosk.Model("models/vosk-model-small-en-us-0.15")

def callback(indata, frames, time, status):
    q.put(bytes(indata))

def listen():
    """
    Listen to the user's voice using Vosk and return the recognized text.
    Handles interruptions and logs all recognized text for review.
    """
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            rec = vosk.KaldiRecognizer(model, 16000)
            print("Listening...")
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        print("User said:", text)
                        # Log the transcript for review
                        with open("stt_transcript.log", "a") as f:
                            f.write(f"{datetime.now()} USER: {text}\n")
                        return text
    except KeyboardInterrupt:
        print("[STT] Interrupted by user.")
        return None
    except Exception as e:
        print(f"[STT] Error: {e}")
        return None

# For testing
if __name__ == "__main__":
    print(listen())
