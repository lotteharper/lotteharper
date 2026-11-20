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
    from django.conf import settings
    from django.db import transaction
    from live.models import VideoFrame
    from lotteh.celery import process_live as live_task

    error = None
    with transaction.atomic():
        frame = VideoFrame.objects.select_for_update().get(id=frame_id)
        if not frame.processed:
            try:
                _process_live(camera_id, frame)
            except Exception as exc:
                error = exc
    if error:
        live_task.apply_async([camera_id, frame_id], countdown=settings.LIVE_INTERVAL / 1000 * 8)
        raise error


def _process_live(camera_id, frame):
    from django.conf import settings
    from live.models import VideoCamera, get_file_path
    import os, shutil, zipfile
    from shell.execute import run_command
    camera = VideoCamera.objects.get(id=camera_id)
    if frame.compressed:
        with zipfile.ZipFile(frame.frame.path, 'r') as zip_ref:
            name = 'frame.' + camera.mimetype.split(';')[0]
            if zip_ref.namelist() != [name]:
                raise ValueError("Invalid video segment archive")
            new_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, name))
            with zip_ref.open(name) as source, open(new_path, 'wb') as target:
                shutil.copyfileobj(source, target)
        old_path = frame.frame.path
        frame.frame = new_path
        frame.compressed = False
        frame.save()
        os.remove(old_path)
    if not frame.frame.name.lower().endswith('.mp4'):
        path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        run_command('ffmpeg -i {} -crf 0 -c:v libx264 {}'.format(frame.frame.path, path))
        if not os.path.isfile(path) or not os.path.getsize(path):
            raise RuntimeError("Video segment conversion failed")
        old_path = frame.frame.path
        frame.frame = path
        frame.save()
        os.remove(old_path)
    transcript = ''
    if camera.speech_only or camera.censor_audio:
        #from live.speech_detection import detect_speech
        #contains_speech, transcript = detect_speech(frame.frame.path, camera.vad_mode)
        from audio.transcription import get_transcript
        transcript, fingerprint = get_transcript(frame.frame.path, save_fingerprint=False)
        if transcript and camera.speech_only: frame.contains_speech = True
    if camera.server_moderation or ((frame.recording.first() and (frame.recording.first().frames.count() % settings.VIDEO_SEGMENTS_PER_MODERATION)) == 0):
        from live.nude import is_nude_segment_fast
        frame.safe = not is_nude_segment_fast(frame.frame.path)
    if settings.NUDITY_CENSOR and not frame.safe:
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from security.censor_video import censor_video_nude, censor_video_nude_fast
        censor_video_nude_fast(frame.frame.path, op_path, scale=settings.NUDITY_CENSOR_SCALE)
        old_path = frame.frame.path
        frame.frame = op_path
        frame.save()
        os.remove(old_path)
    if frame.contains_speech and camera.censor_audio:
        from better_profanity import profanity
    if frame.contains_speech and camera.censor_audio and profanity.contains_profanity(transcript):
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from audio.censor import censor_video_audio
        result = censor_video_audio(frame.frame.path, op_path)
        if result:
            old_path = frame.frame.path
            frame.frame = op_path
            frame.save()
            os.remove(old_path)
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
    import datetime as dt
    from django.conf import settings
    from django.db import transaction
    from django.utils import timezone
    from live.models import VideoRecording
    from lotteh.celery import process_recording as recording_task

    delay = settings.LIVE_INTERVAL / 1000 * 3
    with transaction.atomic():
        recording = VideoRecording.objects.select_for_update().get(id=id)
        if recording.processing or recording.processed:
            return
        remaining = (recording.last_frame + dt.timedelta(seconds=delay) - timezone.now()).total_seconds()
        if remaining > 0:
            transaction.on_commit(lambda: recording_task.apply_async([id], countdown=remaining))
            return
        recording.processing = True
        recording.save(update_fields=['processing'])

    try:
        _process_recording(recording)
    except Exception:
        VideoRecording.objects.filter(id=id, processed=False).update(processing=False)
        recording_task.apply_async([id], countdown=delay)
        raise


def _process_recording(recording):
    embed_logo = False
    from live.concat import concat
    from live.duration import get_duration
    from audio.transcription import get_transcript
    from live.models import VideoRecording, get_file_path, VideoCamera
    from django.conf import settings
    import os
    from shell.execute import run_command
    camera = VideoCamera.objects.filter(user=recording.user, name=recording.camera).order_by('-last_frame').first()
    if not camera:
        raise RuntimeError("Recording camera not found")
    for frame in recording.frames.filter(processed=False):
        process_live(camera.id, frame.id)
    recording.save()
    path = os.path.join(settings.BASE_DIR, 'media', get_file_path(recording, 'file.mp4'))
    recording.file = concat(recording, path, embed_logo, camera)
    try:
        run_command('sudo chmod 777 ' + str(recording.file.path))
    except: pass
    if (recording.file and os.path.exists(recording.file.path)) != True:
        raise RuntimeError("Recording concatenation failed")
    recording.duration = get_duration(recording.file.path)
    recording.transcript, recording.fingerprint = get_transcript(recording.file.path)
    recording.save()
    if False and camera.bucket:
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
        try:
            os.remove(recording.file_processed.path)
        except: pass
        recording.file = None
    recording.processed = True
    recording.processing = False
    recording.public = recording.frames.filter(public=False).count() == 0
    recording.save()
    for frame in recording.frames.all(): frame.delete_video()
    recording.frames.clear()

