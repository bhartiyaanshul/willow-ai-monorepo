import pyttsx3
import uuid

def text_to_speech(text):
    filename = f"reply_{uuid.uuid4().hex}.wav"
    engine = pyttsx3.init()
    engine.save_to_file(text, filename)
    engine.runAndWait()
    return filename
