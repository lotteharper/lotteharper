def get_transcript(filename, save_fingerprint=True):
    import speech_recognition as sr
    from tts.slice import convert_video_to_audio_ffmpeg
    import os
    from audio.fingerprinting import save_fingerprint
    # open the file
    path = convert_video_to_audio_ffmpeg(filename)
    fingerprint = None
    if save_fingerprint:
        fingerprint = save_fingerprint(path)
    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        # listen for the data (load audio to memory)
        audio_data = r.record(source)
        # recognize (convert from speech to text)
        try:
            res = r.recognize_google(audio_data, show_all=True)
            if 'alternative' in res:
                res = res['alternative'][0]['transcript']
            os.remove(path)
            return res if res else '', fingerprint
        except:
            import traceback
            print(traceback.format_exc())
            return '', fingerprint

def get_wav_transcript(path):
    import speech_recognition as sr
    import os
    # open the file
    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        # listen for the data (load audio to memory)
        audio_data = r.record(source)
        # recognize (convert from speech to text)
        try:
            res = r.recognize_google(audio_data, show_all=True)
            if 'alternative' in res:
                res = res['alternative'][0]['transcript']
            os.remove(path)
            return res if res else ''
        except:
            return ''
