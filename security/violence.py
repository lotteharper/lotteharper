EXCLUDED_LABELS = [
    # outdoor cases
#    'people walking on a street',
#    'buildings',
    'fight on a street',
    'fire on a street',
    'street violence',
#    'road',
#    'car crash',
#    'cars on a road',
#    'car parking area',
#    'cars',
    # indoor cases
#    'office environment',
#    'office corridor',
    'violence in office',
    'fire in office',
#    'people talking',
#    'people walking in office',
#    'person walking in office',
#    'group of people',
]

def detect(image):
    import sys
    sys.path.append('/home/team/lotteh/violence-detection/')
    from model import Model
    import cv2
    model = Model()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    label = model.predict(image=image)['label']
    if label != 'Unknown' and label in EXCLUDED_LABELS: return True
    return False

SCALE_FACTOR = 0.1

def resize_with_aspect_ratio(image, width=None, height=None):
    import cv2
    h, w = image.shape[:2]
    aspect_ratio = w / h
    if width is None:
        new_height = int(height / aspect_ratio)
        resized_image = cv2.resize(image, (height, new_height))
    else:
        new_width = int(width * aspect_ratio)
        resized_image = cv2.resize(image, (new_width, width))
    return resized_image

def detect_lowres(image):
    global SCALE_FACTOR
    h, w = image.shape[:2]
    m = w
    if h > w: m = h
    img = resize_with_aspect_ratio(image, int(m * SCALE_FACTOR))
    return detect(img)
