import moviepy as mp
import uuid
from django.conf import settings
import os

def get_temp_wav(mp4_file):
    # Insert Local Video File Path
    clip = mp.VideoFileClip(mp4_file)
    output_wav = os.path.join(settings.BASE_DIR, "temp/data/{}.wav".format(str(uuid.uuid4())))
    # Insert Local Audio File Path
    clip.audio.write_audiofile(output_wav,codec='pcm_s16le')
    return output_wav

def get_temp_mp3(mp4_file):
    # Insert Local Video File Path
    clip = mp.VideoFileClip(mp4_file)
    output_mp3 = os.path.join(settings.BASE_DIR, "temp/data/{}.mp3".format(str(uuid.uuid4())))
    # Insert Local Audio File Path
    clip.audio.write_audiofile(output_mp3)
    return output_mp3
