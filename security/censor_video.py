FREQUENCY = 200
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

def censor_video_nude(input_file, output_file, scale=1):
    from nudenet import NudeDetector
    detector = NudeDetector()
#    print(dets)
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
    import cv2, pytesseract
    import numpy as np
    from moviepy import *
    clip = VideoFileClip(input_file)
    vidcap = cv2.VideoCapture(input_file)
    vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
    index = 0
    while has_frames:
        has_frames, image = vidcap.read()
        if has_frames:
            dim = (int(image.shape[0] * scale), int(image.shape[1] * scale), image.shape[2])
            small_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
            transparent_img = np.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=np.uint8)
            dets = detector.detect(small_image)
            for det in dets:
                if not det['class'] in banned_nudity and not settings.BLUR_ALL_NUDE:
                    continue
                if not should: continue
                box = det['box']
                x1 = int(box[0]/scale - vs)
                y1 = int(box[1]/scale - vs)
                x2 = int(box[2]/scale + box[0] + vs)
                y2 = int(box[3]/scale + box[1] + vs)
                if x1 < 0: x1 = 0
                if y1 < 0: y1 = 0
                if y2 > image.shape[0]: y2 = image.shape[0]
                if x2 > image.shape[1]: x2 = image.shape[1]
                part = image[y1:y2, x1:x2]
                part = cv2.GaussianBlur(part, (bc + 1,bc + 1), bc*2)
                transparent_imag[y1:y2, x1:x2] = part
            im = ImageClip(transparent_img, duration=FREQUENCY/1000.0)
            clip = CompositeVideoClip([clip, im.set_start(index * FREQUENCY).with_duration(FREQUENCY)])
        index = index + 1
    clip.write_videofile(output_path)


def censor_video_text(input_file, output_file, scale=1):
    import cv2, pytesseract
    import numpy as np
    from moviepy import *
    clip = VideoFileClip(input_file)
    vidcap = cv2.VideoCapture(input_file)
    vidcap.set(cv2.CAP_PROP_POS_MSEC, FREQUENCY)
    index = 0
    while has_frames:
        has_frames, image = vidcap.read()
        if has_frames:
            dim = (int(image.shape[0] * scale), int(image.shape[1] * scale), image.shape[2])
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
                im = ImageClip(transparent_img, duration=FREQUENCY/1000.0)
                clip = CompositeVideoClip([clip, im.set_start(index * FREQUENCY).with_duration(FREQUENCY)])
        index = index + 1
    clip.write_videofile(output_path)
