def add_logo_to_video(video_path, new_video_path, vendor):
    import moviepy as mp
    from moviepy.video.fx import Margin
    from django.conf import settings
    import os
    import glob
    video = mp.VideoFileClip(video_path)
    video.with_fps(30)
    logo = (mp.ImageClip(os.path.join(settings.BASE_DIR, "media/", vendor.vendor_profile.logo.path))
              .with_duration(video.duration)
              .with_fps(30)
              .resized(height=int(video.w/13)) # if you need to resize...
              .with_effects([Margin(margin_size=10,opacity=0)])
              .with_position(("left","bottom")))
    text_logo = create_text_overlay(video, vendor.vendor_profile.video_intro_text, str(os.path.join(settings.MEDIA_ROOT, vendor.vendor_profile.video_intro_font.path)) if vendor.vendor_profile.video_intro_font and os.path.exists(vendor.vendor_profile.video_intro_font.path) else None, vendor.vendor_profile.video_intro_color)
    final = mp.CompositeVideoClip([video, logo, text_logo])
    final.with_fps(30)
    final.write_videofile(new_video_path)
    for f in glob.glob(str(settings.BASE_DIR) + '*TEMP_MPY_wvf_snd.mp3'):
        os.remove(f)
    return new_video_path

def create_text_overlay(video, text, font_path, font_color):
    import moviepy as mp
    from django.conf import settings
    import os
    from moviepy.video.fx.CrossFadeIn import CrossFadeIn
    from moviepy.video.fx.CrossFadeOut import CrossFadeOut
    text_clip = mp.TextClip(text=text, method='label', margin=((video.w/13)+25, 15), color=font_color, font_size=video.w/20, font=str(os.path.join(settings.BASE_DIR, 'static/fonts/quick-kiss.ttf')) if not font_path else font_path)
    tc_width, tc_height = text_clip.size
    text_clip = text_clip.with_start(0).with_position(('left', 'bottom')).with_duration(15 if video.duration >= 15 else video.duration).with_fps(30)
    text_clip = CrossFadeIn(0.3).apply(text_clip)
    text_clip = CrossFadeOut(0.6).apply(text_clip)
    return text_clip
