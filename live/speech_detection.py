def detect_speech(audio_path, vad_mode):
    import os, json, traceback
    import uuid
    from django.utils.crypto import get_random_string
    import sys
    import os
    import wave
    from tts.recognize import audio_to_text
    from django.conf import settings
    from pydub import AudioSegment
    import subprocess
    import os
    import sys
    import ffmpeg
#    from tts.silence import remove_silence
    from scipy.io import wavfile
    from pydub.silence import split_on_silence
    from django.contrib import messages
    from feed.middleware import get_current_request
    from django.core.files.base import ContentFile
    import librosa
    from tts.slice import convert_wav
    from vosk import Model, KaldiRecognizer
    r = get_current_request()
    output_wav = os.path.join(settings.BASE_DIR, "temp/data/{}.wav".format(str(uuid.uuid4())))
    os.system('ffmpeg -i {} -ac 1 -ar 16000 {}'.format(audio_path, output_wav))
#    wave_path = convert_wav(audio_path)
    wf = wave.open(output_wav, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print('Not a wav')
        return
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
    if len(results) == 0:
        from audio.transcription import get_wav_transcript
        results = get_wav_transcript(output_wav)
    os.remove(output_wav)
    return len(results) > 0

def detect_speech_old(input_mp4, vad_mode):
    PASSING_SCORE = 90
#    import moviepy as mp
    import uuid
    from django.conf import settings
    import os
#    clip = mp.VideoFileClip(input_mp4)
    output_wav = os.path.join(settings.BASE_DIR, "temp/data/{}.wav".format(str(uuid.uuid4())))
    os.system('ffmpeg -i {} -ac 1 -ar 8000 {}'.format(input_mp4, output_wav))
#    from pydub import AudioSegment
#    audio_file = AudioSegment.from_file(output_wav, format='wav')
#    normalized_audio = audio_file.normalize()
#    output_wav2 = os.path.join(settings.BASE_DIR, "temp/data/{}.wav".format(str(uuid.uuid4())))
#    normalized_audio = audio_file.normalize()
#    quieter_audio = audio_file - 40
#    quieter_audio.export(output_wav2, format='wav')
#    os.remove(output_wav)
#    clip.audio.write_audiofile(output_wav, codec='pcm_s16le')
    import webrtcvad
    import wave
    vad = webrtcvad.Vad(int(vad_mode))
#    vad.set_mode(3)
    with wave.open(output_wav, "rb") as wf:
        sample_rate = wf.getframerate()
        audio_data = wf.readframes(wf.getnframes())
    frame_duration = 30
    frame_bytes = int(sample_rate * frame_duration / 1000) * 2
    output = 0
    count = 0
    for i in range(0, len(audio_data), frame_bytes):
        frame = audio_data[i:i + frame_bytes]
        if len(frame) == frame_bytes:
            is_speech = vad.is_speech(frame, sample_rate)
            if is_speech: output += 1
            count += 1
    os.remove(output_wav)
    if (output / count * 1.0) > (PASSING_SCORE/100.0): return True
    return False
