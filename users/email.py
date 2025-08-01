from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.template import Template, Context
from django.conf import settings
from feed.models import Post
import traceback

def send_verification_email(user):
    User = get_user_model()
    mail_subject = '[{}] Activate your account.'.format(settings.SITE_NAME)
    message = render_to_string('users/verification_email.txt', {
        'the_site_name': settings.SITE_NAME,
        'model_name': User.objects.get(id=settings.MY_ID).profile.name,
        'user': user,
        'domain': settings.DOMAIN,
        'protocol': 'https',
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    html_message = render_to_string('users/verification_email.html', {
        'the_site_name': settings.SITE_NAME,
        'model_name': User.objects.get(id=settings.MY_ID).profile.name,
        'user': user,
        'domain': settings.DOMAIN,
        'protocol': 'https',
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    send_html_email(user, mail_subject, html_message)


def send_email(address, mail_subject, html_message, attachments=None):
    to_email = address
    username = address
    if to_email == '':
        return None
    unsub_link = settings.BASE_URL
    html_message = '<!DOCTYPE html><html><head><link rel="shortcut-icon" type="image/x-icon" href="{}/email/static/lotteh.png" /></head><body><div style="background-color: {}; padding: 5px; border-radius: 10px;"><img alt="Our company logo" src="{}{}" style="border-radius: 50%; width: 40px; height: 40px;"></img><div style="display: inline-block; padding: 10px; position: relative; top:-10px;"><h1>{}</h1></div></div><div style="background-color: {}; white-space: pre-wrap;">\n'.format(settings.BASE_URL, settings.HEADER_COLOR, settings.BASE_URL, settings.EMAIL_ICON_URL, settings.SITE_NAME, settings.BACKGROUND_COLOR) + html_message + '\n\n</div><div style="background-color: {}; padding: 10px; border-radius: 10px;"><p style="display: inline;">If you would like to stop receiving these emails, please <a href="{}" title="Unsubscribe from all {} emails">unsubscribe</a>.</p>  <b>Email: <a href="mailto:{}">{}</a> Phone: <a href="tel:{}">{}</a> - <a href="{}" title="Visit {}">{}</a></div></body></html>'.format(settings.FOOTER_COLOR, unsub_link, settings.SITE_NAME, settings.EMAIL_ADDRESS, settings.EMAIL_ADDRESS, settings.PHONE_NUMBER, phone_number_format(settings.PHONE_NUMBER), settings.BASE_URL, settings.SITE_NAME, settings.BASE_URL)
    msg = EmailMultiAlternatives(mail_subject, strip_tags(html_message), settings.DEFAULT_FROM_EMAIL, [to_email], headers={'List-Unsubscribe' : '<' + unsub_link + '>'},)
    msg.attach_alternative(html_message, "text/html")
    if attachments:
        for a in attachments:
            msg.attach_file(a)
    try:
        msg.send(fail_silently=False)
    except:
        print(traceback.format_exc())

def phone_number_format(phone):
    return '+{} ({}) {}-{}'.format(phone[1:2], phone[2:5], phone[5:8], phone[-4:])

def send_html_email(user, mail_subject, html_message, attachments=None):
    to_email = user.email
    username = user.username
    if to_email == '':
        return None
    unsub_link = settings.BASE_URL + user.profile.create_unsubscribe_link()
    html_message = '<!DOCTYPE html><html><head><link rel="shortcut-icon" type="image/x-icon" href="{}/email/static/lotteh.png" /></head><body><div style="background-color: {}; padding: 5px; border-radius: 10px;"><img alt="Our company logo" src="{}{}" style="border-radius: 50%; width: 40px; height: 40px;"></img><div style="display: inline-block; padding: 10px; position: relative; top:-10px;"><h1>{}</h1></div></div><div style="background-color: {}; white-space: pre-wrap;">\n'.format(settings.BASE_URL, settings.HEADER_COLOR, settings.BASE_URL, settings.EMAIL_ICON_URL, settings.SITE_NAME, settings.BACKGROUND_COLOR) + html_message + '\n\n</div><div style="background-color: {}; padding: 10px; border-radius: 10px;"><p style="display: inline;">If you would like to stop receiving these emails, please <a href="{}" title="Unsubscribe from all {} emails">unsubscribe</a>.</p>  <b>Email: <a href="mailto:{}">{}</a> Phone: <a href="tel:{}">{}</a> - <a href="{}" title="Visit {}">{}</a></div></body></html>'.format(settings.FOOTER_COLOR, unsub_link, settings.SITE_NAME, settings.EMAIL_ADDRESS, settings.EMAIL_ADDRESS, settings.PHONE_NUMBER, phone_number_format(settings.PHONE_NUMBER), settings.BASE_URL, settings.SITE_NAME, settings.BASE_URL)
    msg = EmailMultiAlternatives(mail_subject, strip_tags(html_message), settings.DEFAULT_FROM_EMAIL, [to_email], headers={'List-Unsubscribe' : '<' + unsub_link + '>'},)
    msg.attach_alternative(html_message, "text/html")
    if attachments:
        for a in attachments:
            msg.attach_file(a)
    profile = user.profile
    try:
        msg.send(fail_silently=False)
        if not profile.email_valid:
            profile.email_valid=True
            profile.save()
    except:
        print(traceback.format_exc())
        profile.email_valid=False
        profile.save()

def send_html_email_backend(sender, to_email, mail_subject, html_message, attachments=None):
    from django.core.mail.backends.smtp import EmailBackend
    backend = EmailBackend(host=settings.DOMAIN, port=settings.EMAIL_PORT, username=sender.profile.bash, password=sender.profile.email_password, use_tls=True)
    username = user.username
    if to_email == '':
        return None
    unsub_link = settings.BASE_URL + user.profile.create_unsubscribe_link()
    html_message = '<!DOCTYPE html><html><head><link rel="shortcut-icon" type="image/x-icon" href="{}/email/static/lotteh.png" /></head><body><div style="background-color: {}; padding: 5px; border-radius: 10px;"><img alt="Our company logo" src="{}{}" style="border-radius: 50%; width: 40px; height: 40px;"></img><div style="display: inline-block; padding: 10px; position: relative; top:-10px;"><h1>{}</h1></div></div><div style="background-color: {}; white-space: pre-wrap;">\n'.format(settings.BASE_URL, settings.HEADER_COLOR, settings.BASE_URL, settings.EMAIL_ICON_URL, settings.SITE_NAME, settings.BACKGROUND_COLOR) + html_message + '\n\n</div><div style="background-color: {}; padding: 10px; border-radius: 10px;"><p style="display: inline;">If you would like to stop receiving these emails, please <a href="{}" title="Unsubscribe from all {} emails">unsubscribe</a>.</p>  <b>Email: <a href="mailto:{}">{}</a> Phone: <a href="tel:{}">{}</a> - <a href="{}" title="Visit {}">{}</a></div></body></html>'.format(settings.FOOTER_COLOR, unsub_link, settings.SITE_NAME, settings.EMAIL_ADDRESS, settings.EMAIL_ADDRESS, settings.PHONE_NUMBER, phone_number_format(settings.PHONE_NUMBER), settings.BASE_URL, settings.SITE_NAME, settings.BASE_URL)
    msg = EmailMultiAlternatives(mail_subject, strip_tags(html_message), '{} <{}@{}>'.format(sender.profile.name, sender.profile.bash, settings.MAIL_NAME), [to_email], connection=backend)
    msg.attach_alternative(html_message, "text/html")
    if attachments:
        for a in attachments:
            msg.attach_file(a)
    profile = user.profile
    try:
        msg.send(fail_silently=False)
        if not profile.email_valid:
            profile.email_valid=True
            profile.save()
    except:
        print(traceback.format_exc())
        profile.email_valid=False
        profile.save()

def send_html_email_template(user, mail_subject, html_message, attachments=None):
    posts = Post.objects.filter(author__id=settings.MY_ID, enhanced=True, private=False, public=True, published=True, recipient=None).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=posts).order_by('?').first()
    photo_url = post.get_face_blur_thumb_url(True)
    template = Template(html)
    subjtemplate = Template(subject)
    ctxt = {'username': user.username, 'name': user.profile.name, 'preferred_name': user.profile.preferred_name, 'email': user.email, 'base_url': settings.BASE_URL, 'model_name': User.objects.get(id=settings.MY_ID).profile.name, 'site_name': settings.SITE_NAME, 'photo': photo_url, 'time': timezone.now().strftime("%B %d, %Y %I:%M:%S %p")}
    context = Context(ctxt)
    renderedtemplate = template.render(context)
    subjcontext = Context(ctxt)
    subjrenderedtemplate = subjtemplate.render(subjcontext)
    send_html_email(user, subjrenderedtemplate, renderedtemplate, attachments=None)

def sendwelcomeemail(request, user):
    User = get_user_model()
    html = open('{}/users/welcome_email.html'.format(settings.BASE_DIR)).read()
    subject = 'Welcome to ' + settings.SITE_NAME + ', {{ username }}!'
    template = Template(html)
    subjtemplate = Template(subject)
    context = Context({'username': user.username, 'base_url': settings.BASE_URL, 'model_name': User.objects.get(id=settings.MY_ID).profile.name, 'site_name': settings.SITE_NAME})
    renderedtemplate = template.render(context)
    subjcontext = Context({'username': user.username})
    subjrenderedtemplate = subjtemplate.render(subjcontext)
    send_html_email(user, subjrenderedtemplate, renderedtemplate)
