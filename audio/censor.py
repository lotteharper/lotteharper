import os, json, traceback
from django.utils.crypto import get_random_string
import sys
import os
import wave
from django.conf import settings
from pydub import AudioSegment
import subprocess
import os
import sys
import ffmpeg
from tts.silence import remove_silence
from scipy.io import wavfile
from pydub.silence import split_on_silence
from django.contrib import messages
from feed.middleware import get_current_request
from django.core.files.base import ContentFile
import librosa

toffset = 200

def get_wav_transcript(path):
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
        return text

def convert_video_to_audio_ffmpeg(video_file, output_ext="wav"):
    """Converts video to audio directly using `ffmpeg` command
    with the help of subprocess module"""
    filename, ext = os.path.splitext(video_file)
    subprocess.call(["ffmpeg", "-y", "-i", video_file, f"{filename}.{output_ext}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT)
    return video_file.split('.')[0] + '.wav'

def convert_wav(audio_path):
    return convert_video_to_audio_ffmpeg(audio_path)

def censor_audio(audio_path, output_path, format='wav'):
    from vosk import Model, KaldiRecognizer

    wave_path = convert_wav(audio_path)
    proc_file = AudioSegment.from_wav(wave_path)
    wf = wave.open(wave_path, "rb")
    sample_rate = wf.getframerate()
    model = Model(lang="en-us")
    rec = KaldiRecognizer(model, sample_rate)
    results = []
    frame_size = 1000  # frames per chunk
    ms_per_frame = 1000.0 / sample_rate
    time_ms = 0
    while True:
        data = wf.readframes(frame_size)
        if len(data) == 0:
            break
        time_ms += frame_size * ms_per_frame
        try:
            if rec.AcceptWaveform(data):
                try:
                    text = json.loads(rec.Result())["partial"]
                except:
                    text = ''
                results.append((time_ms, text.strip()))
            else:
                try:
                    text = json.loads(rec.PartialResult())["partial"]
                except:
                    text = ''
                results.append((time_ms, text.strip()))
        except: pass

    if len(results) == 0:
        os.remove(wave_path)
        return False
    ltime = 0
    combined_sounds = AudioSegment.empty()
    beep = AudioSegment.from_wav(os.path.join(settings.BASE_DIR, 'media/sounds/', 'censor-beep.wav'))

    from better_profanity import profanity
    for time_ms, word in results:
        segment = proc_file[ltime:int(time_ms)]
        if profanity.contains_profanity(word):
            # Replace the segment with beep, matching the segment length
            beep_segment = beep[:len(segment)] if len(beep) > len(segment) else beep + AudioSegment.silent(duration=len(segment)-len(beep))
            combined_sounds += beep_segment
        else:
            combined_sounds += segment
        ltime = int(time_ms)

    # Add remaining audio if any
    if ltime < len(proc_file):
        combined_sounds += proc_file[ltime:]

    combined_sounds.export(output_path, format=format)
    return output_path

def censor_audio_old(audio_path, output_path, format='wav'):
    from vosk import Model, KaldiRecognizer
    r = get_current_request()
    wave_path = convert_wav(audio_path)
    print('Wav exists? {}'.format(str(os.path.exists(wave_path))))
    proc_file = AudioSegment.from_wav(wave_path)
    wf = wave.open(wave_path, "rb")
#    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
#        print('Not a wav')
#        return
    duration = wf.getnframes()/float(wf.getframerate())
    model = Model(lang="en-us")
    rec = KaldiRecognizer(model, wf.getframerate())
    results = list()
    last = ''
    time = 0
    while True:
        data = wf.readframes(1000)
        time = time + 20
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            text = ''
            try:
                text = json.loads(rec.Result())["partial"]
            except:
                text = ''
            if len(text) > len(last):
                temp = text
                text = text[(len(last)):]
                last = temp
                results.append((time, text.strip()))
        else:
            text = ''
            try:
                text = json.loads(rec.PartialResult())["partial"]
            except:
                text = ''
            if len(text) > len(last):
                temp = text
                text = text[(len(last)):]
                last = temp
                results.append((time, text.strip()))
    print(results)
    ltime = 0
    ltext = ''
    lword = ''
    count = 0
    last_word = ''
    msg = 'Detected word(s) '
    combined_sounds = AudioSegment.empty()
    from better_profanity import profanity
    beep = AudioSegment.from_wav(os.path.join(settings.BASE_DIR, 'media/sounds/', 'censor-beep.wav'))
    for time, word in results:
        if count >= 0:
            msg = msg + word + ' at ' + str(time) + ', '
            try:
                current_audio = proc_file[ltime:time]
                if True or profanity.contains_profanity(word):
                    beep_segment = beep[:len(current_audio)] if len(beep) > len(current_audio) else beep + AudioSegment.silent(duration=len(current_audio)-len(beep))
                    combined_sounds += beep_segment
                else:
                    combined_sounds += current_audio
                last_word = lword
            except:
                print(traceback.format_exc())
        ltime = time
        lword = word
        count = count + 1
    print(results)
    if len(results) == 0:
        combined_sounds = proc_file
        return wave_path
    if ltime < len(proc_file):
        combined_sounds += proc_file[ltime:]
    combined_sounds.export(output_path, format=format)
    return output_path

def censor_video_audio(video_path, out_path):
    import uuid
    censor_path = os.path.join(settings.BASE_DIR, 'temp/{}-censor.wav'.format(uuid.uuid4()))
    censored_path = censor_audio(video_path, censor_path)
    if censored_path:
        res = os.path.exists(censored_path)
        print(res)
    #    if not res: return
        from audio.addtovideo import replace_audio
        replace_audio(video_path, censored_path, out_path)
    #    os.remove(censored_audio)
        return out_path
    return False

def slice_audio_to_word(user, recording, word_name, last_word, next_word, path, start, end):
    random = get_random_string(length=8)
    write_path = os.path.join(settings.BASE_DIR, 'media/words/', random + '-' + word_name + '.wav')
    newAudio = AudioSegment.from_wav(path)
    newAudio = newAudio[start:end]
    newAudio.export(write_path, format="wav")
    remove_silence(write_path)
    from .models import Word
    the_word = Word.objects.create(file=write_path[len(settings.MEDIA_ROOT):], word=word_name, last_word=last_word, next_word=next_word, user=user, recording=recording)
    from nltk.corpus import wordnet as wn
    try:
        the_word.word_type = wn.synsets(word_name)[0].pos()
        the_word.next_word_type = wn.synsets(next_word)[0].pos()
        the_word.last_word_type = wn.synsets(lasxt_word)[0].pos()
    except: pass
    the_word.save()
    towrite = the_word.file_bucket.storage.open(the_word.file.path, mode='wb')
    with the_word.file.open('rb') as file:
        towrite.write(file.read())
    towrite.close()
    the_word.file_bucket = the_word.file.path
    the_word.save()
    os.remove(the_word.file.path)
