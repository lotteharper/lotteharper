def send_photo_email(user, post):
    from users.email import send_html_email
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.template.loader import render_to_string
    from security.crypto import encrypt_cbc
    from feed.models import Post
    import datetime
    photo_url = post.get_image_url()
    html_message = render_to_string('feed/photo_email.html', {
        'site_name': settings.SITE_NAME,
        'user': user,
        'domain': settings.DOMAIN,
        'protocol': 'https',
        'photos': [photo_url],
        'model_name': post.author.profile.name,
        'message': encrypt_cbc(self.auction_message, settings.AES_KEY) if post.date_auction > timezone.now() - datetime.timedelta(days=31*3) else 'Thank you again for your purchase.',
    })
    import os
    if post.file and not os.path.exists(post.file.path): post.download_file()
    att = [post.file.path if post.file else None]
    send_html_email(user, 'Your Item From {}, {}'.format(settings.SITE_NAME, user.username), html_message, attachments=att)

def send_photos_email(user, posts):
    from users.email import send_html_email
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.template.loader import render_to_string
    from feed.models import Post
    import datetime
    photo_urls = []
    files = []
    from barcode.tests import document_scanned
    authenticated = document_scanned(user)
#    print(posts)
    import os
    messages = []
    for photo in posts:
        if photo.file and not os.path.exists(photo.file.path): photo.download_file()
        if authenticated and (photo.private or not photo.public):
            if photo.image: photo_urls = photo_urls + [photo.get_image_url()]
            if photo.file: files = files + [photo.file.path]
        elif not (photo.private or not photo.public):
            if photo.image: photo_urls = photo_urls + [photo.get_image_url()]
            if photo.file: files = files + [photo.file.path]
        post = photo
        from security.crypto import decrypt_cbc
        from django.conf import settings
        if post.date_auction > timezone.now() - datetime.timedelta(days=31*3):
            messages = messages + [decrypt_cbc(post.auction_message, settings.AES_KEY)]
    if not messages: messages += ['Thank you again for your purchase.']
    html_message = render_to_string('feed/photo_email.html', {
        'site_name': settings.SITE_NAME,
        'user': user,
        'domain': settings.DOMAIN,
        'protocol': 'https',
        'photos': photo_urls,
        'model_name': posts[0].author.profile.name,
        'messages': messages,
    })
    att = files
    send_html_email(user, 'Your Items From {}, {}'.format(settings.SITE_NAME, user.username), html_message, attachments=att)
