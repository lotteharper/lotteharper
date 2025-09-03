import requests, json, base64, os, traceback
from django.conf import settings

def check_all_offsite():
    from feed.models import Post
    for post in Post.objects.all():
        check_offsite(post)

def check_offsite(post):
    if post.image_offsite and not get_offsite_image(post.image_offsite.split('.')[-2].split('/')[-1]):
        post.image_offsite = None
        post.save()
    if post.image_thumb_offsite and not get_offsite_image(post.image_thumb_offsite.split('.')[-2].split('/')[-1]):
        post.image_thumb_offsite = None
        post.save()

def get_offsite_image(hash):
    headers = {"Authorization": "Client-ID {}".format(settings.IMGUR_ID)}
    r = requests.get('https://api.imgur.com/3/image/{}'.format(hash), headers=headers)
    print(r.text)
    j = r.json()
    return (not 'status' in j) or (j['status'] != 404)

def get_image(image_path):
    from PIL import Image
    base_width = settings.MAX_RED_IMAGE_DIMENSION
    img = Image.open(image_path)
    wpercent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    return img

def resize_image(image_path):
    from PIL import Image
    img = Image.open(image_path)
    output_size = (settings.MAX_RED_IMAGE_DIMENSION, settings.MAX_RED_IMAGE_DIMENSION)
    max = img.width
    if img.height < img.width:
        max = img.height
    from feed.crop import crop_center
    img = crop_center(img,max,max)
    try:
        img.thumbnail(output_size)
        return img
    except: pass
    return None

def get_as_base64(url):
    return base64.b64encode(requests.get(url).content)

def upload_photo(path, key=None, user=None, post=None):
    from io import BytesIO
    buffered1 = BytesIO()
    im1 = get_image(path)
    im1.save(buffered1, format="PNG")
    image1 = base64.b64encode(buffered1.getvalue())
    buffered2 = BytesIO()
    im2 = resize_image(path)
    im2.save(buffered2, format="PNG")
    image2 = base64.b64encode(buffered2.getvalue())
    if not len(image1) > 0: return None, None
    from django.conf import settings
    if user:
        refresh_imgur(user)
        key = user.vendor_profile.imgur_token
    i1 = upload(image1, key=key if key else settings.IMGUR_ID, user=user, post=post) if len(image1) > 0 else None
    if user:
        refresh_imgur(user)
        key = user.vendor_profile.imgur_token
    i2 = upload(image2, key=key if key else settings.IMGUR_ID, user=user, post=post) if len(image2) > 0 else None
    return i1, i2

def upload(base64_data, key=None, user=None, post=None):
#    b64data = 'data:image/png;base64,' + base64_data.decode('utf-8')
    data = {
        'image': base64_data,
        'type': 'base64',
        'title': '{} - {}'.format(settings.SITE_NAME, settings.AUTHOR_NAME),
        'description': settings.BASE_DESCRIPTION + ' - from {}'.format(settings.STATIC_DOMAIN),
    }
    headers = {"Authorization": ("Client-ID" if not key else "Bearer") + " {}".format(settings.IMGUR_ID if not key else key)}
    out = requests.post('https://api.imgur.com/3/image', data=data, headers=headers)
    print(out)
    print(out.text)
    j = out.json()
    image_id = j['data']['id']
    try:
        if user and post and not post.private and post.public:
            refresh_imgur(user)
            key = user.vendor_profile.imgur_token
            headers = {"Authorization": "Bearer {}".format(key)}
            data = {
                'title': settings.SITE_NAME + ' | ' + post.content.split('\n')[0][:255],
                'mature': 0 if post.public and not post.private else 1,
            }
            j2 = requests.post('https://api.imgur.com/3/gallery/image/{}'.format(image_id), headers=headers, data=data)
            print(j2)
            print(j2.text)
    except: pass
    if j['status'] == 200:
        return j['data']['link']
    return None

def upload_photo_old(path):
    files = {'image': ('{}.png'.format(settings.DOMAIN), open(path, 'rb'), 'image/png')}
    out = requests.post('https://api.imgbb.com/1/upload?key={}'.format(settings.IMAGE_HOST_KEY), files=files)
    print(out)
    j = out.json()
    if j and 'data' in j:
        return j['data']['image']['url'], j['data']['thumb']['url']
    return None, None

MAX_UPLOAD = 1500

def upload_photo_cloudinary(path):
    import cloudinary, base64, json, uuid, cv2
    import cloudinary.uploader
    from cloudinary.utils import cloudinary_url
    from django.conf import settings
    cloudinary.config(
        cloud_name = settings.CLOUDINARY_CLOUD_NAME,
        api_key = settings.CLOUDINARY_API_KEY,
        api_secret = settings.CLOUDINARY_API_SECRET,
        secure=True
        )
    image = cv2.imread(path)
    height, width = image.shape[:2]
    new_width = width
    new_height = height
    greatest = width if width > height else height
    if greatest > MAX_UPLOAD:
        new_width = int(width * (MAX_UPLOAD/greatest))
        new_height = int(height * (MAX_UPLOAD/greatest))
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    retval, buffer = cv2.imencode('.png', resized_image)
    data = 'data:image/png;base64,' + base64.b64encode(buffer).decode('utf-8')
#    print(data[:100])
    uid = str(uuid.uuid4())
    upload_result = cloudinary.uploader.upload(data, public_id=uid)
    auto_crop_url, _ = cloudinary_url(uid, width=500, height=500, crop="auto", gravity="auto")
#    print(json.dumps(upload_result))
#    print(upload_result["secure_url"])
    return str(upload_result['secure_url']), str(auto_crop_url)

def refresh_imgur(user):
    refresh_token = user.vendor_profile.imgur_refresh
    import requests, json
    from django.conf import settings
    payload = {
        'client_id': settings.IMGUR_ID,
        'client_secret': settings.IMGUR_SECRET,
        'refresh_token': refresh_token,
        'grant_type': "refresh_token"
    }
    resp = requests.post('https://api.imgur.com/oauth2/token', data=payload)
    print(resp)
    print(resp.text)
    j = resp.json()
    user.vendor_profile.imgur_refresh = j['refresh_token']
    user.vendor_profile.imgur_token = j['access_token']
    user.vendor_profile.save()


def upload_post(post):
    import traceback
    from feed.models import Post
    if post.image_bucket or (post.image and os.path.exists(post.image.path)):
        post.download_photo()
        if not post.image_censored or not os.path.exists(post.image_censored.path):
            post.image_censored = None
            post.image_offsite = None
            post.save()
            post = Post.objects.get(id=post.id)
            post.get_blur_url(gen=True)
            post = Post.objects.get(id=post.id)
        from django.utils import timezone
        import datetime
        anonymous = not post.author.vendor_profile.imgur_time > timezone.now() - datetime.timedelta(minutes=60*24*7)
        try:
            i1, i2 = upload_photo(post.image.path if post.public and not post.private else post.image_censored.path, post.author.vendor_profile.imgur_token if not anonymous else None, post.author if not anonymous else None, post)
            post.image_offsite = i1
            post.image_thumb_offsite = i2
        except OSError:
            print(traceback.format_exc())
            try:
                post.image = None
                post.image_censored = None
                post.save()
                post.download_photo()
                post = Post.objects.get(id=post.id)
                if not post.image_censored or not os.path.exists(post.image_censored.path):
                    post.image_censored = None
                    post.image_censored_bucket = None
                    post.image_offsite = None
                    post.save()
                    post = Post.objects.get(id=post.id)
                    post.get_blur_url(True)
                    post = Post.objects.get(id=post.id)
                i1, i2 = upload_photo(post.image.path if post.public and not post.private else post.image_censored.path, post.author.vendor_profile.imgur_token if not anonymous else None, post.author if not anonymous else None, post)
                post.image_offsite = i1
                post.image_thumb_offsite = i2
            except: print(traceback.format_exc())
        post.offsite = True
        post.save()
        from lotteh.celery import async_check_upload
        async_check_upload.apply_async(countdown=60*5, args=[post.id])
#        except: print(traceback.format_exc())
        print('Uploaded post ({}). - {}'.format(post.id, post.image_offsite))
        return True
    return False

def upload_posts():
    from feed.models import Post
    for post in Post.objects.filter(published=True, image_offsite=None, offsite=False).order_by('-date_posted'):
        if not (post.image_offsite and len(post.image_offsite) > 0) and post.image: # or (post.image and os.path.exists(post.image.path):
            try: upload_post(post)
            except:
                print(traceback.format_exc())

def upload_post_async():
    from feed.models import Post
    for post in Post.objects.filter(published=True, image_offsite=None).order_by('-date_posted'):
        if not (post.image_offsite and len(post.image_offsite) > 0) and post.image: # or (post.image and os.path.exists(post.image.path):
            try:
                upload_post(post)
            except:
                print(traceback.format_exc())
            return
