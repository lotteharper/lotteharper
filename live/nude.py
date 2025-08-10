import os, uuid
from django.conf import settings

FAST_SCALE = 0.3


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
#        "FACE_FEMALE",
#        "FACE_MALE",
#        "BELLY_EXPOSED",
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


def is_nude_segment_fast(input_path):
    import cv2, os
    vidcap = cv2.VideoCapture(input_path)
    success = True
    firstimg = None
    first = True
    while success:
        success,image = vidcap.read()
        if first and success:
            try:
                return is_nude_fast_cv2(image)
            except: pass
    return None
