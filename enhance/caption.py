import re, os
from feed.models import Post
replace = {'man': 'woman', 'boy': 'woman', 'his': 'her', 'man\'s': 'woman\'s', 'men': 'women', 'him': 'her', 'beard': 'piercing', 'knife': 'pose', 'mustache': 'makeup', 'a makeup': 'makeup', 'with makeup': 'wearing makeup', 'dog': 'phone'}

def caption_post(post):
    print(post.id)
    if True: #post.uploaded:
        if post.image and not post.content:
            try:
                if not os.path.exists(post.image.path) and (post.image or post.image_bucket): post.download_photo()
            except: post.download_photo()
#            post = Post.objects.get(id=post.id)
            if post.image and os.path.exists(post.image.path):
                from feed.caption import caption_image
                caption_text = ''
                try:
                    caption_text = caption_image(post.image.path, prompt='What\'s in this photo?')
                except:
                    try:
                        from feed.caption_old import caption_image as caption_old
                        caption_text = caption_old(post.image.path)
                    except: pass
                for key, value in replace.items():
                    caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
                    caption_text = re.sub('\s' + key + '\.', ' ' + value + '.', caption_text)
                    caption_text = re.sub('\s' + key + '\,', ' ' + value + ',', caption_text)
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
    for post in Post.objects.filter(content='', public=True).exclude(image=None).order_by('-date_posted'):
        if post.image:
            p = caption_post(post)
            if p: return
    for post in Post.objects.filter(content='', public=False).exclude(image=None).order_by('-date_posted'):
        if post.image:
            p = caption_post(post)
            if p: return
