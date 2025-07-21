FREQUENCY = 1
AVERAGE = 100
EXTRA = 1
MIN_TEXT = 4

def censor_video_all(input_file, output_file, scale=1):
    import os, uuid
    from django.conf import settings
    path = os.path.join(settings.BASE_DIR, 'temp/', '{}.mp4'.format(str(uuid.uuid4())))
    censor_video_text(input_file, path, scale=scale)
    censor_video_nude(path, output_file, scale=scale)
    os.remove(path)
    return output_file

def get_width(img):
    import cv2
    h, w, c = img.shape
    return w

MIN_BC = 30

MIN_BC_NUDE = 60

def censor_video_nude(input_file, output_file, scale=1):
    from django.conf import settings
    import cv2, traceback, math
    from nudenet import NudeDetector
    detector = NudeDetector()
#    print(dets)
    banned_nudity = [
        "FACE_FEMALE",
        "FACE_MALE",
        "BELLY_EXPOSED",
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
    import cv2, pytesseract
    import numpy as np
    import moviepy as mp
    clip = mp.VideoFileClip(input_file)
    vidcap = cv2.VideoCapture(input_file)
    vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
    vidcap.set(cv2.CAP_PROP_FPS, FREQUENCY)
    actual_fps = vidcap.get(cv2.CAP_PROP_FPS)
    print(FREQUENCY)
    index = 0
    vs = 42
    has_frames = True
    bc = 30
    count = 0
    first = False
    transparent_img = None
    x1 = 0
    y1 = 0
    w = 0
    h = 0
    while has_frames:
        has_frames, image = vidcap.read()
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = rgb_image
        if has_frames:
            print(index)
            if not first:
                first = True
                bc = math.floor(get_width(image)/1000) * 2
                if bc < MIN_BC: bc = MIN_BC_NUDE
                vs = math.floor(get_width(image)/1000) * 5
            if index%50 == 0:
                dim = (int(image.shape[1] * scale), int(image.shape[0] * scale))
                small_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
                transparent_img = np.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=np.uint8)
                dets = detector.detect(small_image)
                for det in dets:
                    print(det['class'])
                    if (not det['class'] in banned_nudity) and (not settings.BLUR_ALL_NUDE):
                        continue
                    box = det['box']
    #                print(box)
                    x1 = int(box[0]/scale - vs)
                    y1 = int(box[1]/scale - vs)
                    w = int(box[2]/scale + box[0] + vs*2)
                    h = int(box[3]/scale + box[1] + vs*2)
                    if x1 < 0: x1 = 0
                    if y1 < 0: y1 = 0
                    if y1+h > image.shape[0]: h-=(y1+h-image.shape[0])
                    if x1+w > image.shape[1]: w-=(w1+w-image.shape[1])
            finished = cv2.blur(image[y1:y1+h, x1:x1+w], (AVERAGE, AVERAGE))
            transparent_img[y1:y1+h, x1:x1+w] = finished
            im = mp.ImageClip(transparent_img, duration=1.0/FREQUENCY)
            clip = mp.CompositeVideoClip([clip, im.with_start(index * 1.0/actual_fps).with_duration(1.0/actual_fps)])
        index = index + 1
    clip.write_videofile(output_file)

POOL_FRAMES = 100

def censor_video_nude_fast(input_file, output_file, scale=1):
    from django.conf import settings
    import cv2, traceback, math
    from nudenet import NudeDetector
    detector = NudeDetector()
#    print(dets)
    banned_nudity = [
        "FACE_FEMALE",
        "FACE_MALE",
        "BELLY_EXPOSED",
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
    import cv2, pytesseract
    import numpy as np
    import moviepy as mp
    clip = mp.VideoFileClip(input_file)
    vidcap = cv2.VideoCapture(input_file)
    vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
    vidcap.set(cv2.CAP_PROP_FPS, FREQUENCY)
    actual_fps = vidcap.get(cv2.CAP_PROP_FPS)
    print(FREQUENCY)
    index = 0
    vs = 42
    has_frames = True
    bc = 30
    count = 0
    first = False
    transparent_img = None
    x1 = 0
    y1 = 0
    w = 0
    h = 0
    while has_frames:
        has_frames, image = vidcap.read()
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = rgb_image
        if has_frames:
            print(index)
            if not first:
                first = True
                bc = math.floor(get_width(image)/1000) * 2
                if bc < MIN_BC: bc = MIN_BC_NUDE
                vs = math.floor(get_width(image)/1000) * 5
            if index%POOL_FRAMES == 0:
                dim = (int(image.shape[1] * scale), int(image.shape[0] * scale))
                small_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
                transparent_img = np.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=np.uint8)
                dets = detector.detect(small_image)
                for det in dets:
                    print(det['class'])
                    if (not det['class'] in banned_nudity) and (not settings.BLUR_ALL_NUDE):
                        continue
                    box = det['box']
    #                print(box)
                    x1 = int(box[0]/scale - vs)
                    y1 = int(box[1]/scale - vs)
                    w = int(box[2]/scale + box[0] + vs*2)
                    h = int(box[3]/scale + box[1] + vs*2)
                    if x1 < 0: x1 = 0
                    if y1 < 0: y1 = 0
                    if y1+h > image.shape[0]: h-=(y1+h-image.shape[0])
                    if x1+w > image.shape[1]: w-=(w1+w-image.shape[1])
                finished = cv2.blur(image[y1:y1+h, x1:x1+w], (AVERAGE, AVERAGE))
                image[y1:y1+h, x1:x1+w] = finished
                im = mp.ImageClip(image, duration=1.0/FREQUENCY)
                clip = mp.CompositeVideoClip([clip, im.with_start(index * 1.0/actual_fps).with_duration(1.0/actual_fps*POOL_FRAMES)])
        index = index + 1
    clip.write_videofile(output_file)


def censor_video_text(input_file, output_file, scale=1):
    import cv2, pytesseract
    import numpy as np
    import moviepy as mp
    clip = mp.VideoFileClip(input_file)
    vidcap = cv2.VideoCapture(input_file)
    vidcap.set(cv2.CAP_PROP_FPS, FREQUENCY)
    actual_fps = vidcap.get(cv2.CAP_PROP_FPS)
#    vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
    index = 0
    has_frames = True
    while has_frames:
        has_frames, image = vidcap.read()
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = rgb_image
        if has_frames:
            dim = (int(image.shape[1] * scale), int(image.shape[0] * scale))
            small_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
            transparent_img = np.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=np.uint8)
            data = pytesseract.image_to_data(small_image, output_type='dict')
            boxes = len(data['level'])
            for i in range(boxes):
                if len(data['text']) < MIN_TEXT: continue
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                x = int(x / scale)
                y = int(y / scale)
                w = int(w / scale)
                h = int(h / scale)
                x = x - w * extra
                y = y - h * extra
                w = w * extra * 3
                h = h * extra * 3
                if x < 0: x = 0
                if y < 0: y = 0
                if y + h > image.shape[0]: y = image.shape[0]
                if x + w > image.shape[1]: x = image.shape[1]
                img = cv2.blur(image[y:y+h, x:x+w], (AVERAGE, AVERAGE))
                transparent_img[y:y+h, x:x+w] = img
                im = mp.ImageClip(transparent_img, duration=FREQUENCY/1000.0)
                clip = mp.CompositeVideoClip([clip, im.with_start(index * 1.0/actual_fps).with_duration(1.0/actual_fps)])
        index = index + 1
    clip.write_videofile(output_file)

