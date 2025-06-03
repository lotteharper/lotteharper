from moviepy import AudioFileClip, VideoFileClip

def replace_audio(video_path, audio_path, output_filename):
    audio_clip = AudioFileClip(audio_path, audio_path)
    video_clip = VideoFileClip(video_path)
    video_clip.with_audio(audio_clip)
    video_clip.duration = audio_clip.duration
    video_clip.fps = 30
    video_clip.write_videofile(output_filename)
