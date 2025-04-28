
def get_duration(video_path):
    from moviepy import VideoFileClip
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"Error: {e}")
        return 0
