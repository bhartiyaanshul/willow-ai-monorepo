from gtts import gTTS
import uuid
import os
from pydub import AudioSegment

def text_to_speech(text, speed=1.0):
    """
    Convert text to speech using gTTS and pydub. Returns the filename of the generated audio.
    Handles speed adjustment and cleans up temp files.
    """
    try:
        print("🔊 Converting text to speech (gTTS):", text)
        filename = f"reply_{uuid.uuid4().hex}.wav"
        mp3_filename = filename.replace('.wav', '.mp3')
        tts = gTTS(text)
        tts.save(mp3_filename)
        # Convert mp3 to wav for compatibility and adjust speed
        sound = AudioSegment.from_mp3(mp3_filename)
        if speed != 1.0:
            sound = sound._spawn(sound.raw_data, overrides={
                "frame_rate": int(sound.frame_rate * speed)
            }).set_frame_rate(sound.frame_rate)
        sound.export(filename, format="wav")
        os.remove(mp3_filename)
        return filename
    except Exception as e:
        print(f"TTS error: {e}")
        return None

speak = text_to_speech
