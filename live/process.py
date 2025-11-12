from django.contrib.auth.models import User
import os

def update_video_description(user_id, recording_id, video_id, thumbnail_url, original_description, original_title, original_category_id, prompt):
    import os, uuid
    from django.contrib.auth.models import User
    from django.conf import settings
    user = User.objects.get(id=int(user_id))
    op_path = os.path.join(settings.BASE_DIR, 'temp/', '{}.jpg'.format(str(uuid.uuid4())))
    from live.upload import download_image_from_url
    download_image_from_url(thumbnail_url, op_path)
    from live.caption import caption_thumbnail
    thumbnail_caption = caption_thumbnail(str(op_path), prompt=prompt, title=original_title)
#    print('Path exists for download? {}'.format(str(os.path.exists(op_path))))
#    print(thumbnail_caption)
    os.remove(op_path)
    from live.upload import update_description
    from live.models import VideoRecording
    recording = VideoRecording.objects.get(id=int(recording_id))
    update_description(user, recording, video_id, thumbnail_caption + '\n' + original_description, original_title, original_category_id)

def process_live(camera_id, frame_id):
    from tts.slice import convert_wav
    from feed.nude import is_nude_fast
    from security.safety import is_safe_image, is_safe_file
    from django.conf import settings
    from live.models import VideoCamera, VideoFrame, get_file_path, get_still_path
    import os, datetime, uuid, shutil, zipfile
    from django.utils import timezone
    from shell.execute import run_command
    camera = VideoCamera.objects.get(id=camera_id)
    frame = VideoFrame.objects.get(id=frame_id)
    if frame.compressed:
        with zipfile.ZipFile(frame.frame.path, 'r') as zip_ref:
            path = os.path.join(settings.BASE_DIR, '/temp/', str(uuid.uuid4()))
            zip_ref.extractall(path)
            file = os.path.join(path, 'frame.' + camera.mimetype.split(';')[0])
            new_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.' + camera.mimetype.split(';')[0]))
            shutil.copy(file, new_path)
            os.remove(path)
            os.remove(frame.frame.path)
            frame.frame = new_path
            frame.compressed = False
            frame.save()
    frame = VideoFrame.objects.get(id=frame_id)
    if camera.mimetype.split(';')[0] != 'mp4':
        path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        run_command('ffmpeg -i {} -crf 0 -c:v libx264 {}'.format(frame.frame.path, path))
        try:
            os.remove(frame.frame.path)
        except: pass
        frame.frame = path
    transcript = ''
    if camera.speech_only or camera.censor_audio:
        #from live.speech_detection import detect_speech
        #contains_speech, transcript = detect_speech(frame.frame.path, camera.vad_mode)
        from audio.transcription import get_transcript
        transcript, fingerprint = get_transcript(frame.frame.path, save_fingerprint=False)
        if transcript and camera.speech_only: frame.contains_speech = True
    if camera.server_moderation or (frame.recording.first().frames.count() % settings.VIDEO_SEGMENTS_PER_MODERATION) == 0:
        from live.nude import is_nude_segment_fast
        try:
            frame.safe = not is_nude_segment_fast(frame.frame.path)
        except:
            import traceback
            print(traceback.format_exc())
    if settings.NUDITY_CENSOR and not frame.safe:
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from security.censor_video import censor_video_nude, censor_video_nude_fast
        censor_video_nude_fast(frame.frame.path, op_path, scale=settings.NUDITY_CENSOR_SCALE)
        os.remove(frame.frame.path)
        frame.frame = op_path
        frame.save()
    from better_profanity import profanity
    if frame.contains_speech and camera.censor_audio and profanity.contains_profanity(transcript):
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from audio.censor import censor_video_audio
        result = censor_video_audio(frame.frame.path, op_path)
        if result:
            os.remove(frame.frame.path)
            frame.frame = op_path
            frame.save()
    if not frame.safe and settings.NUDITY_FILTER: # or not is_safe_image(frame.still.path):
        frame.public = False
        frame.processed = True
        frame.save()
        return
    if False and frame.animate_video and camera.name == 'private' and camera.user.profile.vendor:
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from live.anime import convert_video_anime
        new_path = convert_video_anime(frame.frame.path, op_path)
        try:
            os.remove(frame.frame.path)
        except: pass
        frame.frame = new_path
    frame.processed = True
    frame.save()

def process_recording(id):
    embed_logo = False
    from live.concat import concat
    from audio.transcription import get_transcript
    from audio.fingerprinting import save_fingerprint, is_in_database
    from live.models import VideoRecording, VideoFrame, get_file_path, VideoCamera
    from django.utils import timezone
    from django.contrib.auth.models import User
    from django.conf import settings
    import os
    from live.still import get_still
    from shell.execute import run_command
    import datetime as dt
    recording = VideoRecording.objects.get(id=id)
    if (recording.last_frame < timezone.now() - dt.timedelta(seconds=(settings.LIVE_INTERVAL/1000) * 12)) and (not (recording.processing or recording.processed)): # 4 (the number is the gap, a larger number adds more length to the recording with a longer gap
        recording.processing = True
        recording.save()
        camera = VideoCamera.objects.filter(user=recording.user, name=recording.camera).order_by('-last_frame').first()
        for frame in recording.frames.filter(processed=False):
            try:
                frame = VideoFrame.objects.get(id=frame.id)
                if not frame.processed:
                    process_live(camera.id, frame.id)
            except:
                import traceback
                print(traceback.format_exc())
        recording.save()
        path = os.path.join(settings.BASE_DIR, 'media', get_file_path(recording, 'file.mp4'))
        recording.file = concat(recording, path, embed_logo, camera)
        try:
            run_command('sudo chmod 777 ' + str(recording.file.path))
        except: pass
        if (recording.file and os.path.exists(recording.file.path)) != True:
            recording.processed = True
            recording.save()
            return
        recording.transcript, recording.fingerprint = get_transcript(recording.file.path)
        recording.save()
        if not camera.bucket:
            recording.processed = True
            recording.save()
        elif False:
            towrite = recording.file_processed.storage.open(recording.file.path, mode='wb')
            with recording.file.open('rb') as file:
                towrite.write(file.read())
            towrite.close()
            recording.file_processed = recording.file.path
        thumbnail = None
        first_frame = recording.frames.first()
        if False and camera.upload and os.path.exists(first_frame.still.path):
            from live.models import get_still_path
            path = os.path.join(settings.BASE_DIR, 'media', get_still_path(first_frame, 'file.png'))
            from feed.anime import convert_photo_anime
            convert_photo_anime(first_frame.still.path, path)
            towrite = recording.thumbnail_bucket.storage.open(path, mode='wb')
            with open(path, 'rb') as file:
                towrite.write(file.read())
            towrite.close()
            recording.thumbnail_bucket = path
            os.remove(path)
            thumbnail = recording.thumbnail_bucket.url
        if camera.upload:
            recording.prompt = camera.prompt
            recording.save()
            from live.upload import upload_recording
            upload_recording(recording, camera)
        recording = VideoRecording.objects.get(id=recording.id)
        if recording.uploaded:
            try:
                os.remove(recording.file.path)
            except: pass
            recording.file = None
        recording.processed = True
        recording.public = recording.frames.filter(public=False).count() == 0
        recording.save()
        for frame in recording.frames.all(): frame.delete_video()
        recording.frames.clear()
