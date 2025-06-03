import os, uuid
from django.conf import settings

FAST_SCALE = 0.3

def get_nude_fast(image_path):
    from PIL import Image
    img = Image.open(image_path)
    w, h = img.size
    width = int(w*FAST_SCALE)
    height = int(h*FAST_SCALE)
    img = img.resize((width, height))
    from nudenet import NudeDetector
    detector = NudeDetector()
    return detector.detect(img)


def is_nude_fast(image_path):
    from PIL import Image
    img = Image.open(image_path)
    w, h = img.size
    width = int(w*FAST_SCALE)
    height = int(h*FAST_SCALE)
    img = img.resize((width, height))
    result = is_nude(img)
    return result

def is_nude_fast_cv2(image_cv2):
    from PIL import Image
    img = Image.fromarray(image_cv2)
    w, h = img.size
    width = int(w*FAST_SCALE)
    height = int(h*FAST_SCALE)
    img = img.resize((width, height))
    result = is_nude(img)
    return result

def is_nude(image_path):
    from nudenet import NudeDetector
    detector = NudeDetector()
    dets = detector.detect(image_path)
    banned_nudity = [
        "FEMALE_GENITALIA_COVERED",
        "BUTTOCKS_EXPOSED",
        "FEMALE_BREAST_EXPOSED",
        "FEMALE_GENITALIA_EXPOSED",
        "MALE_BREAST_EXPOSED",
        "ANUS_EXPOSED",
        "MALE_GENITALIA_EXPOSED",
        "ANUS_COVERED",
        "BUTTOCKS_COVERED",
    ]
    for det in dets:
        if det['class'] in banned_nudity: return True
    return False

#    import nude
#    return nude.is_nude(image_path)


def is_nude_file(video_path, fast=True):
    import nude, cv2
    from django.conf import settings
    cap = cv2.VideoCapture(video_path)
    count = 0
    success = True
    while success:
        success, image = cap.read()
        if count%(30 * settings.NUDITY_FILTER_SECONDS) == 0:
             if fast:
                 if is_nude_fast_cv2(image): return True
             else:
                 if is_nude(image): return True
        count+=1
    return False

def is_nude_video(video_path):
    try:
        return is_nude_file(video_path, fast=True)
    except: return False
