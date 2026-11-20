import io
import shutil
import tempfile
import zipfile

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def save_video_segment(camera, timestamp, video_id, confirmation_id, content):
    from live.models import VideoCamera, VideoFrame, VideoRecording
    from live.still import is_still
    from lotteh.celery import process_live, process_recording

    captured = parse_datetime(timestamp)
    if not captured or timezone.is_naive(captured) or not video_id or len(video_id) > 21 or not confirmation_id or not content:
        raise ValueError("Invalid video segment metadata")

    compressed = camera.compress_video
    video_extension = camera.mimetype.split(';', 1)[0]
    extension = 'zip' if compressed else video_extension
    frame = VideoFrame(
        user=camera.user, time_captured=captured, compressed=compressed,
        confirmation_id=confirmation_id, adjust_pitch=camera.adjust_pitch,
        animate_video=camera.animate_video,
    )
    frame.frame.save('frame.' + extension, ContentFile(content), save=False)
    try:
        if compressed:
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    if archive.namelist() != ['frame.' + video_extension]:
                        raise ValueError("Invalid video segment archive")
                    with archive.open(archive.infolist()[0]) as source, tempfile.NamedTemporaryFile(suffix='.' + video_extension) as video:
                        shutil.copyfileobj(source, video)
                        video.flush()
                        _, frame.difference = is_still(video.name)
            except zipfile.BadZipFile as exc:
                raise ValueError("Invalid video segment archive") from exc
        else:
            _, frame.difference = is_still(frame.frame.path)
        frame.save()
    except Exception:
        frame.frame.delete(save=False)
        raise

    camera.last_frame = timezone.now()
    camera.confirmation_id = confirmation_id
    camera.save(update_fields=['last_frame', 'confirmation_id'])

    with transaction.atomic():
        if camera.recording:
            VideoCamera.objects.select_for_update().get(id=camera.id)
            recording = VideoRecording.objects.select_for_update().filter(
                user=camera.user, camera=camera.name, camera_id=video_id,
                processing=False, processed=False,
            ).order_by('-last_frame').first()
            limit = camera.video_length_minutes * 60
            if camera.short_mode:
                limit = min(limit, settings.LIVE_SHORT_SECONDS)
            if not recording or recording.frames.count() * settings.LIVE_INTERVAL / 1000 >= limit:
                recording = VideoRecording.objects.create(
                    user=camera.user, camera=camera.name, last_frame=timezone.now(), camera_id=video_id
                )
            recording.frames.add(frame)
            recording.last_frame = timezone.now()
            recording.save()
            transaction.on_commit(lambda: process_recording.apply_async(
                [recording.id], countdown=settings.LIVE_INTERVAL / 1000 * 6
            ))

        transaction.on_commit(lambda: process_live.delay(camera.id, frame.id))
    return frame

