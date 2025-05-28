from gtts import gTTS
import uuid
import os

def text_to_speech(text):
    print("🔊 Converting text to speech (gTTS):", text)
    filename = f"reply_{uuid.uuid4().hex}.wav"
    mp3_filename = filename.replace('.wav', '.mp3')
    print("🔊 Saving audio to:", filename)
    tts = gTTS(text)
    tts.save(mp3_filename)
    # Convert mp3 to wav for compatibility
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_mp3(mp3_filename)
        sound.export(filename, format="wav")
        os.remove(mp3_filename)
    except ImportError:
        print("pydub not installed, returning mp3 file instead of wav.")
        return mp3_filename
    return filename

speak = text_to_speech
