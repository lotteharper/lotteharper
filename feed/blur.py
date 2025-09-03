import os
from django.conf import settings

def get_width(image_path):
    import cv2
    h, w, c = cv2.imread(image_path).shape
    return w

MIN_BC = 30

MIN_BC_NUDE = 60

def blur_faces(input_path):
    import cv2, traceback, math
    bc = math.floor(get_width(input_path)/1000) * 2
    if bc < MIN_BC: bc = MIN_BC
    image = cv2.imread(input_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    try:
        face_detect = cv2.CascadeClassifier(os.path.join(settings.BASE_DIR, 'feed/haarcascade_frontalface_default.xml'))
        face_data = face_detect.detectMultiScale(image, 1.3, 5)
        image = cv2.imread(input_path)
        for (x, y, w, h) in face_data:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), 2)
            roi = image[y:y+h, x:x+w]
            roi = cv2.GaussianBlur(roi, (bc + 1,bc + 1), bc*2)
            image[y:y+roi.shape[0], x:x+roi.shape[1]] = roi
        cv2.imwrite(input_path, image)
    except:
        print(traceback.format_exc())


import requests
import json

import base64

def write_image(imgstring, filename):
    import cv2, traceback
    imgdata = base64.b64decode(imgstring)
    with open(filename, 'wb') as f:
        f.write(imgdata)

def blur_nude(input_path, output_path):
    import cv2, traceback, math
    bc = math.floor(get_width(input_path)/1000) * 4
    if bc < MIN_BC_NUDE: bc = MIN_BC_NUDE
    image = cv2.imread(input_path)
    try:
        roi = cv2.GaussianBlur(image, (bc + 1,bc + 1), bc*2)
        cv2.imwrite(output_path, roi)
        return output_path
    except:
        print(traceback.format_exc())


def blur_nude_only(input_path, output_path):
    import cv2, traceback, math
    from nudenet import NudeDetector
    detector = NudeDetector()
    image = cv2.imread(input_path)
    res = detector.detect(input_path)
    bc = math.floor(get_width(input_path)/1000) * 4
    vs = get_width(input_path)/50
    if vs > 100: vs = 100
    if bc < MIN_BC_NUDE: bc = MIN_BC_NUDE
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
    for box in res:
        if not box['class'] in banned_nudity and not settings.BLUR_ALL_NUDE: continue
        box = box['box']
#        print(box)
        x1 = int(box[0] - vs)
        y1 = int(box[1] - vs)
        x2 = int(box[2] + box[0] + vs)
        y2 = int(box[3] + box[1] + vs)
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0
        if y2 > image.shape[0]: y2 = image.shape[0]
        if x2 > image.shape[1]: x2 = image.shape[1]
#        print('x1: {}, y1: {}, x2: {}, y2: {}'.format(x1, y1, x2, y2))
        part = image[y1:y2, x1:x2]
        part = cv2.GaussianBlur(part, (bc + 1,bc + 1), bc*2)
        image[y1:y2, x1:x2] = part
    cv2.imwrite(output_path, image)

def blur_nude_old(input_path, output_path):
    params = {
        'concepts': 'nudity',
        'api_user': settings.SIGHTENGINE_USER,
        'api_secret': settings.SIGHTENGINE_SECRET
    }
    files = {'media': open(input_path, 'rb')}
    r = requests.post('https://api.sightengine.com/1.0/transform.json', files=files, data=params)
    output = json.loads(r.text)
    if output['status'] == 'success':
        data = output['transform']['base64']
        output_path = output_path + '.' + output['transform']['content-type'].split('/')[1]
        write_image(data, output_path)
        return output_path
