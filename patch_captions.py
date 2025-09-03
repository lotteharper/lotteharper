import os, sys, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from feed.models import Post

def patch_uncaptioned_posts():
    for post in Post.objects.filter(private=True, content__icontains='sorry, but i can\'t'):
        post.download_photo()
        from feed.caption_old import caption_image as caption_old
        post = Post.objects.get(id=post.id)
        post.content = caption_old(post.image.path)
        post.save()

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

for post in Post.objects.filter(content__length__lte=1000):
    print(post.content)
    post.content = post.content.replace('. .', '.') #augment_text(post, post.content)
    post.save()
