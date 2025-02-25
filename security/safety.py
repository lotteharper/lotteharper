from django.conf import settings

def is_safe_image(path):
    from face.deep import verify_age
    if not verify_age(path): return False
    import cv2
    from .violence import detect_lowres
    if detect_lowres(cv2.imread(path)): return False
    return True

FREQUENCY = 200
AVERAGE = 100
SCALE = 0.4

def is_safe_file(path, scale=settings.DEFAULT_SAFETY_SCALE):
    from face.deep import verify_age_cv2
    import cv2
    from .violence import detect
    global FREQUENCY
    global AVERAGE
    global SCALE
    import magic
    if magic.from_file(path, mime=True).split('/')[0] != 'video': return False # Audio is safe?
    try:
        vidcap = cv2.VideoCapture(path)
        vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
        index = 0
        while has_frames:
            has_frames, image = vidcap.read()
            if has_frames:
                dim = (int(image.shape[0] * SCALE), int(image.shape[1] * SCALE), image.shape[2])
                small_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
                if not verify_age_cv2(small_image): return False
                if detect(small_image): return False
    except: return False
    return True
