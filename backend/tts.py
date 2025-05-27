# backend/tts.py
from TTS.api import TTS

tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

def speak(text, filename="output.wav"):
    tts.tts_to_file(text=text, file_path=filename)
    return filename
