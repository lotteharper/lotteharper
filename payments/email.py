def send_tip_email(user, model, tip, crypto, network):
    from users.email import send_html_email
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.template.loader import render_to_string
    from webpush import send_group_notification
    from users.tfa import send_user_text
    from feed.models import Post
    posts = Post.objects.filter(author__id=settings.MY_ID, enhanced=True, private=False, public=True, published=True, recipient=None).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:500]
    post = Post.objects.filter(id__in=posts).exclude(image_offsite=None).order_by('?').first()
    photo_url = post.image_offsite
    days = 3
    from payments.apis import get_crypto_price
    tip = format(get_crypto_price(crypto) * float(tip), '.2f')
    for user in [user]:
        html_message = render_to_string('payments/tip_email.html', {
            'site_name': settings.SITE_NAME,
            'user': user,
            'model': model,
            'tip': tip,
            'crypto': crypto,
            'network': network,
            'domain': settings.DOMAIN,
            'protocol': 'https',
            'photo': photo_url,
        })
        send_html_email(user, 'Thank you for your tip on {}, {}'.format(settings.SITE_NAME, user.username), html_message)
