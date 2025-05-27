# backend/stt.py
import queue
import sounddevice as sd
import vosk
import sys
import json

q = queue.Queue()

model = vosk.Model("models/vosk-model-small-en-us-0.15")

def callback(indata, frames, time, status):
    q.put(bytes(indata))

def listen():
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
                    return text

# For testing
if __name__ == "__main__":
    print(listen())
