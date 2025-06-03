def concat(recording, output_path, embed_logo):
    from .models import get_file_path
    from subprocess import check_output
    import uuid
    import subprocess
    import os, glob, shutil
    from django.conf import settings
    from shell.execute import run_command
    from django.core.files.base import ContentFile
    if recording.frames.count() == 0:
        recording.delete()
        return
    import moviepy as moviepy
    from live.logo import add_logo_to_video
    import zipfile
    filename = os.path.join(settings.BASE_DIR, 'temp', str(uuid.uuid4()) + '.txt')
    inputs = ''
    is_safe = True
    from live.models import VideoFrame, VideoCamera
    from lotteh.celery import process_live
    camera = VideoCamera.objects.filter(user=recording.user, name=recording.camera).order_by('-last_frame').first()
    for frame in recording.frames.filter(processed=False).order_by('time_captured'):
        frame = VideoFrame.objects.get(id=frame.id)
        if not frame.processed: process_live(camera.id, frame.id)
        frame = VideoFrame.objects.get(id=frame.id)
        if not frame.safe: is_safe = False
    recording.safe = is_safe
    recording.save()
    from live.models import VideoRecording
    recording = VideoRecording.objects.get(id=recording.id)
    for frame in recording.frames.order_by('time_captured'):
        if frame.frame: inputs = inputs + 'file \'' + frame.frame.path + '\'\n'
    if len(inputs) == 0:
        recording.delete()
        return
    with open(filename, 'w') as f:
        f.writelines(inputs)
    f.close()
    #ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4
#    cmd = 'ffmpeg -f concat -safe 0 -i {} -c copy {}'.format(filename, output_path).split(' ')
    try:
        cmd = 'ffmpeg -f concat -safe 0 -i {} -c copy {}'.format(filename, output_path).split(' ')
        check_output(cmd)
        os.remove(filename)
    except:
        try:
            shutil.copy(recording.frames.first().frame.path, output_path)
        except: return
#    run_command('sudo chown love:users ' + str(output_path))
#    cmd = 'ffmpeg -i {} -crf 1 -c:v libx264 {}.mp4'.format(filename, output_path).split(' ')
#    check_output(cmd)
#    os.remove(output_path)
    if camera.embed_logo and embed_logo:
        output_path = str(output_path) + ''
        new_video_path = output_path.split('.')[0] + '-2.mp4'
        ret_path = add_logo_to_video(output_path, new_video_path, recording.user)
        os.remove(output_path)
        recording.file = ret_path
    else: recording.file = output_path
    if camera.adjust_pitch and camera.name == 'private' and camera.user.profile.vendor:
        op_path = os.path.join(settings.MEDIA_ROOT, get_file_path(frame, 'frame.mp4'))
        from live.voice_changer import adjust_video_pitch
        new_path = adjust_video_pitch(recording.file.path, op_path, camera.user.vendor_profile.pitch_adjust)
        try:
            os.remove(new_video_path)
        except: pass
        recording.file = new_path
#    fileList = glob.glob(str(os.path.join(settings.BASE_DIR, '*TEMP_MPY_wvf_snd.mp3*')), recursive=True)
#    for file in fileList:
#        try:
#            os.remove(file)
#        except OSError:
#            print("Error while deleting file")
    recording.save()
    return recording.file.path

def concat_old(recording, output_path):
    clips =[]
    for f in recording.frames.all():
        clips = clips + [moviepy.VideoFileClip(f.frame.path)]
    clip = moviepy.concatenate_videoclips(clips)
    clip.write_videofile(str(output_path) + '.mov', codec='libx264')
    return str(output_path) + '.mov'
