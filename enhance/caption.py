import re, os
from feed.models import Post
from django.utils.html import strip_tags

def detect_ai_error(text):
    if text.startswith('Sorry, but I can\'t'): return True
    if text.startswith('Sorry'): return True
    if text.startswith('I apologize'): return True
    if text.startswith('My apologies'): return True
    return False

def augment_text(post, caption_text):
    pronouns = post.author.vendor_profile.pronouns
    caption_text = caption_text.lower()
    replace = {
        'person': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'person\'s': 'woman\'s' if pronouns == 'Her' else 'man\'s' if pronouns == 'Him' else 'person\'s',
        'they have': 'she has' if pronouns == 'Her' else 'he has' if pronouns == 'Him' else 'they have',
        'they are': 'she is' if pronouns == 'Her' else 'he is' if pronouns == 'Him' else 'they are',
        'man': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'boy': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'his': 'hers' if pronouns == 'Her' else 'his' if pronouns == 'Him' else 'person\'s',
        'man\'s': 'woman\'s' if pronouns == 'Her' else 'man\'s' if pronouns == 'Him' else 'person\'s',
        'men': 'women' if pronouns == 'Her' else 'women\'s' if pronouns == 'Him' else 'people',
        'him': 'her' if pronouns == 'Her' else 'him' if pronouns == 'Him' else 'them',
        'them': 'her' if pronouns == 'Her' else 'him' if pronouns == 'Him' else 'them',
        'their': 'her' if pronouns == 'Her' else 'her' if pronouns == 'Him' else 'their',
        'they\'re': 'she is' if pronouns == 'Her' else 'he is' if pronouns == 'Him' else 'they\'re',
        'beard': 'piercing',
        'knife': 'pose',
        'mustache': 'makeup',
        'a makeup': 'makeup',
        'with makeup': 'wearing makeup',
        'dog': 'phone'
    }
    for key, value in replace.items():
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\.', ' ' + value + '.', caption_text)
        caption_text = re.sub('\s' + key + '\,', ' ' + value + ',', caption_text)
    if post.author.vendor_profile.pronouns != 'They':
        replace = {
            'and are': 'and is',
            'and have': 'and has',
            'also have': 'also has',
        }
    else:
        replace = {}
    for key, value in replace.items():
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\.', ' ' + value + '.', caption_text)
        caption_text = re.sub('\s' + key + '\,', ' ' + value + ',', caption_text)
    caption_text_split = caption_text.split('.')
    op = ''
    for t in caption_text_split[:-1]:
        op = op + ' {}.'.format(t.strip().capitalize())
    return op.strip()

def caption_post(post):
    print(post.id)
    if True: #post.uploaded:
        if post.image or post.image_bucket:
            try:
                if ((not os.path.exists(post.image.path)) or (not post.image)) and post.image_bucket: post.download_photo()
            except:
                import traceback
                print(traceback.format_exc())
                post.download_photo()
            post = Post.objects.get(id=post.id)
            if post.image and os.path.exists(post.image.path):
                from feed.caption import caption_image
                caption_text = ''
                try:
                    caption_text = caption_image(post.image.path, prompt='What\'s in this photo?')
                except:
                    caption_text = ''
                if detect_ai_error(caption_text) or not caption_text:
                    try:
                        from feed.caption_old import caption_image as caption_old
                        caption_text = caption_old(post.image.path)
                    except: pass
                caption_text = augment_text(post, caption_text)
                if caption_text:
                    caption_text = caption_text.strip() + ('.' if not caption_text[-1] == '.' else '')
                    post.content = caption_text
                    post.save()
            if post.image_bucket:
                try:
                    os.remove(post.image.path)
                except: pass
            print(post.content)
            return post.content
    return None

def routine_caption_image():
    print('Captioning image')
    for post in Post.objects.filter(public=True).exclude(image=None).order_by('-date_posted'):
        if post.image and (strip_tags(post.content).encode('utf-8').decode('ascii', errors='ignore').replace(' ', '') == ''):
            print(post.content)
            p = caption_post(post)
            if p: return
    for post in Post.objects.filter(public=False).exclude(image=None).order_by('-date_posted'):
        if post.image and (strip_tags(post.content).encode('utf-8').decode('ascii', errors='ignore').replace(' ', '') == ''):
            p = caption_post(post)
            if p: return
