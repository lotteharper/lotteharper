def process_cart_purchase(user, cart, private=False):
    from django.utils import timezone
    from feed.models import Post
    posts = []
    cart = cart.replace('\\', ',').replace('+', ',').replace('"', '')
    for item in cart.replace('+', ',').split(','):
        s = item.split('=')
        if len(s) < 2: continue
        uid = s[0]
        quant = s[1]
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        if post and not post.private:
            if not post.paid_file:
                post.recipient = user
                post.save()
            else:
                post.paid_users.add(user)
                post.save()
            posts = posts + [post]
        elif post and post.private and document_scanned(user) and private:
            if not post.paid_file:
                post.recipient = user
                post.save()
            else:
                post.paid_users.add(user)
                post.save()
            posts = posts + [post]
    from feed.email import send_photos_email
    send_photos_email(user, posts)

def get_cart_cost(cookies, private=False):
    from django.utils import timezone
    from feed.models import Post
    items = ''
    cookies['cart'] = cookies['cart'].replace('\\', ',').replace('+', ',').replace('"', '')
    try: items = cookies['cart'].replace('+', ',').split(',') if 'cart' in cookies else cookies.split(',')
    except: items = cookies.split(',') if cookies else []
    if not items: items = cookies.split(',')
    price = 0
    if len(items) < 1: return 0
    from django.conf import settings
    for item in items[:-1]:
        s = item.split('=')
        uid = s[0]
        quant = 1
        try:
            quant = s[1]
        except: quant = 1
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        p = post
        if p:
            if (not p.private) or (p.private and private):
                price = price + ((float(p.price) * (quant if settings.ALLOW_MULTIPLE_SALES else 1)) if ((p and (not p.private)) or (p.private and private)) else 0)
    return price

def get_cart(cookies, private=False):
    from django.utils import timezone
    from feed.models import Post
    items = ''
    cookies['cart'] = cookies['cart'].replace('\\', ',').replace('+', ',').replace('"', '')
    try: items = cookies['cart'].replace('+', ',').split(',') if 'cart' in cookies else []
    except: items = cookies.split(',') if cookies else []
    if len(items) < 1: return None
    contents = ''
    from translate.translate import translate
    from feed.middleware import get_current_request
    request = get_current_request()
    for item in items[:-1]:
        s = item.split('=')
        uid = s[0]
        add = '<button onclick="addToCart(\'{}\');" class="btn btn-outline-success" title="{}">{}</button>'.format(uid, translate(request, 'Add another'),translate(request, 'Add another'))
        remove = '<button onclick="removeFromCart(\'{}\');" class="btn btn-outline-danger" title="{}">{}</button>'.format(uid, translate(request, 'Remove'), translate(request, 'Remove'))
        quant = 1
        try:
            quant = s[1]
        except: quant = 1
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        if post:
            image = post.get_image_thumb_url() if not post.private else post.get_blur_thumb_url()
            print(uid)
            print(post)
            if (not post.private) or post.private and private:
                contents = contents + ('<div id="{}"><p>{}: <i id="total{}">{}</i> <img align="left" style="float: left; align: left;" height="100px" width="100px" class="m-2" src="{}">\n{} (<a href="{}" title="{}">{}</a>) - ${} ea {}</p><div style="height: 100px;"></div></div>'.format(post.uuid, translate(request, 'Count'), post.uuid, quant, image, translate(request, 'One photo, video, audio, and/or download'), post.get_absolute_url() if post else '', translate(request, 'See this item'), translate(request, 'See this item'), post.price if post else 0, add + ' ' + remove))
    return contents
