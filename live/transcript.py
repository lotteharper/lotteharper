# Python code to convert video to audio
import moviepy as mp
import speech_recognition as sr
import uuid
from django.conf import settings
import os

def get_transcript(mp4_file):
    # Insert Local Video File Path
    clip = mp.VideoFileClip(mp4_file)
    output_wav = os.path.join(settings.BASE_DIR, "temp/data/{}.wav".format(str(uuid.uuid4())))
    # Insert Local Audio File Path
    clip.audio.write_audiofile(output_wav,codec='pcm_s16le')
    # initialize the recognizer
    r = sr.Recognizer()
    # open the file
    with sr.AudioFile(output_wav) as source:
        # listen for the data (load audio to memory)
        audio_data = r.record(source)
        # recognize (convert from speech to text)
        try:
            res = r.recognize_google(audio_data)
            if 'alternative' in res:
                res = res['alternative'][0]['transcript']
        except: pass
        os.remove(output_wav)
        return res
