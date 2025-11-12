import sys, os, uuid
from moviepy import *
import moviepy as mp
from django.conf import settings
from synthesizer.utils import adjust_pitch
from tts.slice import convert_wav
from live.models import get_file_path
from django.conf import settings

def replace_audio(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video_with_new_audio = video.with_audio(audio)
    video_with_new_audio.write_videofile(output_path)

def adjust_video_pitch(video_path, output_path, semitones=12):
    temp_wav = convert_wav(video_path)
    path = os.path.join(settings.BASE_DIR, 'media/', get_file_path(None, 'file.wav'))
    replace_audio(video_path, adjust_pitch(temp_wav, path, semitones), output_path)
    os.remove(temp_wav)
    os.remove(path)
    return output_path
