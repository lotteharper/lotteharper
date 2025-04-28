from django import template

register = template.Library()

@register.filter('barcodescanned')
def barcodescanned(user):
    from barcode.tests import document_scanned
    return document_scanned(user)

@register.filter('scoretotals')
def scoretotals(user):
    total = 0
    for game in user.created_games.all().union(user.joined_games.all()):
        try:
            if game.player1 == user:
                total = total + int(player1_score)
            else:
                total = total + int(player2_score)
        except: pass
    return total

@register.filter('isabook')
def isabook(postcont):
    return True if '***' in postcont else False

@register.filter('getelementbyindex')
def getelementbyinex(thearr, index):
    return thearr[index]

@register.filter('useablepath')
def useablepath(path):
    # eg /en/test
    return '/'.join(path.split('/')[2:])

@register.filter('char2caps')
def char2caps(input):
    if input[0].isalnum(): return input.capitalize()
    return input[0] + input[1:].capitalize()

@register.filter('islive')
def islive(profile):
    from feed.middleware import get_current_request
    from live.models import VideoCamera
    import datetime
    from django.utils import timezone
    from django.conf import settings
    request = get_current_request()
    cameras = VideoCamera.objects.filter(user=profile.user, name=request.GET.get('camera') if request.GET.get('camera') else 'private')
    if not cameras.first() or not cameras.first().last_frame > timezone.now() - datetime.timedelta(seconds=settings.LIVE_INTERVAL/1000*3): return False
    return True

@register.filter('charcountreader')
def charcountreader(text):
    from django.conf import settings
    return len(text) > settings.POST_READER_LENGTH

@register.filter('trimlength')
def trimlength(text):
    from django.conf import settings
    t = str(text)[0:settings.POST_READER_LENGTH]
    if len(text) > settings.POST_READER_LENGTH: t = t + '...'
    return t

@register.filter('objecttype')
def objecttype(object):
    from feed.models import Post
    if isinstance(object, Post): return 'post'
    return None

@register.filter('urlready')
def urlready(input):
    import urllib.parse
    return urllib.parse.quote_plus(input)

@register.filter('urltouri')
def urltouri(input):
    import urllib.parse
    return urllib.parse.quote_plus(input)

@register.filter('translang')
def translang(content, target):
    from translate.translate import translate
    from feed.middleware import get_current_request
    return translate(get_current_request(), content, target=target)

@register.filter('transpost')
def transpost(target):
    from translate.translate import translate_html
    from feed.middleware import get_current_request
    from feed.models import Post
    from django.conf import settings
    post = Post.objects.get(id=int(target))
    return translate_html(get_current_request(), post.content if len(post.content) < settings.POST_READER_LENGTH else post.content_compiled, get_current_request().LANGUAGE_CODE if get_current_request() and not get_current_request().GET.get('lang', None) else get_current_request().GET.get('lang') if get_current_request() and get_current_request().GET.get('lang', None) else None, post.author.profile.language_code if post.author.profile.language_code else None)

@register.filter('transauthor')
def transauthor(content, target):
    from translate.translate import translate_html
    from feed.middleware import get_current_request
    from feed.models import Post
    from django.conf import settings
    post = Post.objects.get(id=int(target))
    return translate_html(get_current_request(), content, get_current_request().LANGUAGE_CODE if get_current_request() and not get_current_request().GET.get('lang', None) else get_current_request().GET.get('lang') if get_current_request() and get_current_request().GET.get('lang', None) else None, post.author.profile.language_code if post.author.profile.language_code else None)

@register.filter('transmsg')
def transmsg(target):
    from translate.translate import translate_html
    from feed.middleware import get_current_request
    from chat.models import Message
    post = Message.objects.get(id=int(target))
    return translate_html(get_current_request(), post.content, get_current_request().LANGUAGE_CODE if get_current_request() and not get_current_request().GET.get('lang', None) else get_current_request().GET.get('lang') if get_current_request() and get_current_request().GET.get('lang', None) else None, post.sender.profile.language_code if post.sender.profile.language_code else None)

@register.filter('transbio')
def transbio(target):
    from translate.translate import translate_html
    from feed.middleware import get_current_request
    from users.models import Profile
    post = Profile.objects.get(id=int(target))
    return translate_html(get_current_request(), post.bio, get_current_request().LANGUAGE_CODE if get_current_request() and not get_current_request().GET.get('lang', None) else get_current_request().GET.get('lang') if get_current_request() and get_current_request().GET.get('lang', None) else None, post.language_code if post.language_code else None)

def do_blocktrans(parser, token):
    nodelist = parser.parse(('endblocktrans',))
    parser.delete_first_token()
    return TransNode(nodelist)

class TransNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        from translate.translate import translate_html
        from feed.middleware import get_current_request
        return translate_html(get_current_request(), output)

register.tag('blocktrans', do_blocktrans)

@register.filter('sitemapdate')
def sitemapdate(date):
    return date.strftime('%Y-%m-%d')

@register.simple_tag(takes_context=True)
def updateurlparam(context, key, val):
    request = context['request']
    request.GET.mutable = True
    request.GET[key] = val
    from security.middleware import get_qs as get_querystring
    qs = get_querystring(request.GET)
    return qs

@register.filter('trans')
def trans(content):
    from translate.translate import translate
    from feed.middleware import get_current_request
    return translate(get_current_request(), content)

@register.filter('etrans')
def etrans(content):
    from translate.translate import translate
    from feed.middleware import get_current_request
    from django.conf import settings
    return translate(get_current_request(), content, target=get_current_request().LANGUAGE_CODE if get_current_request() and not get_current_request().GET.get('lang') else get_current_request().GET.get('lang') if get_current_request() and get_current_request().GET.get('lang', None) else settings.DEFAULT_LANG, src='en')

@register.filter('stripsender')
def stripsender(sender):
    try:
        return sender.split('<')[1].split('>')[0]
    except: return sender

@register.filter('crypto_earnings_day')
def crypto_earnings_day(trades):
    import datetime
    from django.utils import timezone
    if trades.count() == 0: return 'N/A'
    old = trades.filter(timestamp__lte=timezone.now() - datetime.timedelta(hours=24))
    return trades.last().amount_usd - old.last().amount_usd if old.last() else 0

@register.filter('crypto_earnings_week')
def crypto_earnings_week(trades):
    import datetime
    from django.utils import timezone
    if trades.count() == 0: return 'N/A'
    old = trades.filter(timestamp__lte=timezone.now() - datetime.timedelta(hours=24))
    return trades.last().amount_usd - old.last().amount_usd if old.last() else 0

@register.filter('crypto_earnings_month')
def crypto_earnings_month(trades):
    import datetime
    from django.utils import timezone
    if trades.count() == 0: return 'N/A'
    old = trades.filter(timestamp__lte=timezone.now() - datetime.timedelta(hours=24*7))
    return trades.last().amount_usd - old.last().amount_usd if old.last() else 0

@register.filter('crypto_earnings_year')
def crypto_earnings_year(trades):
    import datetime
    from django.utils import timezone
    if trades.count() == 0: return 'N/A'
    old = trades.filter(timestamp__lte=timezone.now() - datetime.timedelta(hours=24*30))
    if old.count() == 0: return 'N/A'
    return (trades.last().amount_usd - old.last().amount_usd if old.last() else 0) * 12

@register.filter('document_front')
def document_front(user):
    return user.scan.filter(side=True).last().document_isolated.url

@register.filter('document_back')
def document_back(user):
    return user.scan.filter(side=False).last().document_isolated.url

@register.filter('showanswers')
def showanswers(input):
    return '<ul><li>' + '</li><li>'.join(input.replace('[', '').replace(']','').split(',')) + '</li></ul>'

@register.filter('censorcard')
def censorcard(input):
    return '************' + str(input)[12:]

@register.simple_tag(takes_context=True)
def show_ip_counts(context, user):
    from users.middleware import get_current_user
    from feed.middlewarre import get_current_request
    user = get_current_user() if get_current_user() and get_current_user().is_authenticated else None
    if user and user.is_superuser or (hasattr(user, 'profile') and user.profile.vendor):
        if get_current_request() and get_current_request().path.startswith('/face/') or user.is_authenticated:
            return True
    return False

@register.filter('jsonprint')
def jsonprint(input):
    return str(input).replace('{', '{\n').replace(',',',\n')

@register.filter('removejsig')
def removejsig(media):
    import re
    media = str(media).replace('<script src="/static/js/jSignature.min.js"></script>', '')
    media = media.replace('<script src="/static/js/django_jsignature.js"></script>', '')
    media = media.replace('<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.0/jquery.min.js"></script>', '')
    media = re.sub('<script src=\".+jquery\.min\.js\"></script>', '', media)
    return media

@register.filter('splitlines')
def splitlines(content):
    return content.split('\n')

@register.filter('recordingindex')
def recordingindex(index):
    from django.conf import settings
    index = (int(index) - 1) * settings.LIVE_INTERVAL/1000
    return index

@register.simple_tag(takes_context=True)
def get_qs(context):
    from security.middleware import get_qs as get_querystring
    request = context['request']
    return get_querystring(request.GET)[1:]

@register.simple_tag(takes_context=True)
def get_key(context):
    import uuid
    return str(uuid.uuid4())

@register.filter('sub_fee')
def sub_fee(fee):
    import math
    fees = str(fee).split('.')
    if len(fees) > 1:
        fee = fees[0]
        op = ''
        of = len(str(fee))%3
        op = op + str(fee)[0:of] + (',' if of > 0 else '')
        for f in range(math.floor(len(str(fee))/3)):
            op = op + str(fee)[3*f+of:3+3*f+of] + ','
        op = op[:-1]
        return '{}.{}'.format(op, fees[1][:2])
    else:
        op = ''
        of = len(str(fee))%3
        op = op + str(fee)[0:of] + (',' if of > 0 else '')
        for f in range(math.floor(len(str(fee))/3)):
            op = op + str(fee)[3*f+of:3+3*f+of] + ','
        op = op[:-1]
        return op

@register.filter('elegant_sub_fee')
def elegant_sub_fee(fee):
    import math
    fees = str(fee).split('.')
    if len(fees) > 1:
        fee = fees[0]
        op = ''
        of = len(str(fee))%3
        op = op + str(fee)[0:of] + (',' if of > 0 else '')
        for f in range(math.floor(len(str(fee))/3)):
            op = op + str(fee)[3*f+of:3+3*f+of] + ','
        op = op[:-1]
        return '{}.{}'.format(op, fees[1][:1])
    else:
        op = ''
        of = len(str(fee))%3
        op = op + str(fee)[0:of] + (',' if of > 0 else '')
        for f in range(math.floor(len(str(fee))/3)):
            op = op + str(fee)[3*f+of:3+3*f+of] + ','
        op = op[:-1]
        return op

@register.filter('split')
def split(content):
    return content.split('\n')

@register.filter('weekday')
def weekday(time):
    return time.strftime('%A')

@register.filter('sessioncount')
def sessioncount(sessions):
    from .nts import nts as number_to_string
    s = int(sessions)
    se = 'session'
    if s > 1: se = se + 's'
    return number_to_string(int(sessions)) + ' ' + se

@register.filter('phone_number')
def phone_number(phone):
    return '+{} ({}) {}-{}'.format(phone[1:2], phone[2:5], phone[5:8], phone[-4:])

@register.filter('securephone')
def securephone(phone):
    return '+* (***) ***-' + phone[-4:]

def buildlink(c):
    c = c.replace('\'','\\\'')
    return '<a href=\"javascript:say(\'{}\')\">{}</a> '.format(c.lower(), c)

@register.filter('linkspeech')
def linkspeech(text):
    from tts.models import Word
    split = text.split(' ')
    t = ''
    for x in range(len(split)-2):
        l = list()
        c = ''
        for index in range(3):
            if index == 0:
                c = '{} {} {}'.format(split[x], split[x+1], split[x+2])
            if index == 1:
                c = '{} {}'.format(split[x], split[x+1])
            if index == 2:
                c = '{}'.format(split[x])
            words = Word.objects.filter(word=c)
            if words.count() > 0 and not c.startswith('<') or c.endswith('>'):
                l.append(c)
        glen = 0
        gwords = None
        for y, words in enumerate(l):
            if len(words) > glen:
                glen = len(words)
                gwords = words
        if gwords:
            t = t + buildlink(gwords) + ' '
            x = x + len(gwords.split(" "))-1
        else:
            t = t + c + ' '
    return t.strip()

@register.filter('pronouns')
def pronouns(pronoun):
    pn = {'He': 'He/Him/His', 'Her': 'She/Her/Hers', 'They': 'They/Them/Theirs', '': 'They/Them/Theirs'}
    return pn[pronoun]

@register.filter('nts')
def nts(number):
    from .nts import nts as number_to_string
    result = 'no'
    try:
        result = number_to_string(int(number))
        if not result:
            return 'no'
    except:
        return 'no'
    return result

@register.filter('nonts')
def nonts(number):
    from .nts import nts as number_to_string
    if number == '': return 'none'
    if number == None: return 'none'
    if (not (isinstance(number, int) or isinstance(number, str))) or int(number) == 0: return 'none'
    try:
       return number_to_string(int(number))
    except:
        return 'none'

@register.filter('tostring')
def tostring(input):
    return str(input)

@register.filter('stime')
def stime(thetime):
    from django.conf import settings
    import pytz
    from .nts import nts as number_to_string
    from django.utils.dateparse import parse_datetime
    time = parse_datetime(str(thetime))
#    print(time)
    if time == None:
        return '---'
    times = time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%H:%M:%S').split(':')
    o = ' '
    if int(times[1]) < 10:
        o = ' o\' '
    oclock = ' '
    if int(times[1]) == 0:
        oclock = ' o\'clock '
    return (number_to_string(int(times[0])%12) if int(times[0])%12 > 0 else 'twelve') + oclock + ((o + number_to_string(int(times[1]))) if int(times[1]) > 0 else '')

@register.filter('ampm')
def ampm(thetime):
    from django.conf import settings
    import pytz
    from django.utils.dateparse import parse_datetime
    time = parse_datetime(str(thetime))
    if time == None:
        return '---'
    times = time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%H:%M:%S').split(':')
    ampm = 'pm'
    if int(times[0])-12 < 0:
        ampm = 'am'
    return ampm

@register.filter('splitnext')
def splitnext(next):
    out = ''
    try:
        split = next.split('?')[0]
        out = split + '?'
        spl = next.split('?')[1].split('&')
        for s in spl:
            out = out + ((s + '&') if not s.startswith('k=') else '')
        if out[-1] == '&':
            out = out[:-1]
        if out[-1] == '?':
            out = out[:-1]
        return out
    except:
        return next

@register.filter('boolread')
def boolread(bool):
    return 'Y' if bool else 'N'

@register.filter('capitalize')
def capitalize(input):
    return input.capitalize()

@register.filter('urlparams')
def urlparams(page):
    from feed.middleware import get_current_request
    query = get_current_request().GET.copy()
    query['page'] = str(page)
    return query.urlencode()

def highlight_query(query, text):
    from misc.regex import SEARCH_REGEX, ESCAPED_QUERIES
    import re
    if not query: return text
    q = query.split(' ')
    text = ' {} '.format(text)
    dic = {}
    for query in q:
        found = re.findall(SEARCH_REGEX.format(query.lower()), text, flags=re.IGNORECASE)
        for t in found:
            if not t.lower() in ESCAPED_QUERIES:
                dic[t] = '<mark>{}</mark>'.format(t)
    result = {}
    for key, value in dic.items():
        if not key in result:
            result[key] = value
    for key, value in result.items():
        text = text.replace(key, value)
    return text.strip()

def highlight_query_raw(query, text):
    from misc.regex import SEARCH_REGEX, ESCAPED_QUERIES
    import re
    if not query: return text
    q = query.split(' ')
    text = ' {} '.format(text)
    dic = {}
    for query in q:
        found = re.findall(SEARCH_REGEX.format(query.lower()), text, flags=re.IGNORECASE)
        for t in found:
            if not t.lower() in ESCAPED_QUERIES:
                dic[t] = '<mark>{}</mark>'.format(t)
    result = {}
    for key, value in dic.items():
        if not key in result:
            result[key] = value
    for key, value in result.items():
        text = text.replace(key, value)
    return result

@register.filter('highlightsearchquery')
def highlightsearchquery(text):
    from feed.middleware import get_current_request
    request = get_current_request()
    q = request.GET['q']
    from django.conf import settings
    from translate.translate import translate
    oq = q
    q = translate(request, q, target=settings.DEFAULT_LANG)
    from misc.sitemap import languages
    threads = [None] * (len(languages) + 1)
    results = [None] * (len(languages) + 1)
    thread_count = 0
    def highlight_lang(q, lang, text, results, count, src):
        from translate.translate import translate
        from django.conf import settings
        res = highlight_query_raw(translate(None, q, target=lang, src=src), text)
        results[count] = res
    import threading
    src = settings.DEFAULT_LANG
    threads[thread_count] = threading.Thread(target=highlight_lang, args=(q, src, text, results, thread_count, src))
    threads[thread_count].start()
    thread_count += 1
    src = request.LANGUAGE_CODE if request and not request.GET.get('lang', None) else request.GET.get('lang', None) if request.GET.get('lang', None) else settings.DEFAULT_LANG
    for lang in languages:
        threads[thread_count] = threading.Thread(target=highlight_lang, args=(oq, lang, text, results, thread_count, src))
        threads[thread_count].start()
        thread_count += 1
    for i in range(len(threads)):
        if threads[i]: threads[i].join()
    replaced = []
    for result in results:
        if result:
            for key, value in result.items():
                if not key in replaced:
                    text = text.replace(key, value)
                    replaced += [key]
    return text

def get_lang():
    from feed.middleware import get_current_request
    request = get_current_request()
    lang = request.LANGUAGE_CODE
    if(request.GET.get('lang', '') != ''):
        lang = request.GET.get('lang', '')
    if lang == None:
        lang = 'en'
    return lang

@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str) and text.startswith(starts):
        return True
    return False


@register.filter(name='detectlanguage')
def detectlanguage(value):
    from langdetect import detect
    lang = ''
    try:
        lang = detect(value)
    except:
        lang = 'en'
    return lang

@register.filter(name='removelinks')
def removelinks(value):
    import re
    urls = re.findall("(?P<url>https?://[^\s]+)", value)
    dic = {}
    for url in urls:
        dic[url] = '(link hidden)'
    for i, j in dic.items():
        value = value.replace(i, j)
    return value

@register.filter(name='urltouri')
def urltouri(value):
    import urllib.parse
    return urllib.parse.quote(value, safe='')

@register.filter(name='urlready')
def urlready(value):
    return value.replace(" ", "%20")

@register.filter(name='comments')
def comments(value):
    from feed.models import Post
    post = Post.objects.get(id=int(value))
    return False

#    comments = Comment.objects.filter(post=post, public=True).order_by('-date_posted')
#    return comments[:3]

@register.filter(name='addhttpstodomains')
def addhttpstodomains(value):
    escaped_domains = ['manage.py','apps.py','facebook.com', 'models.py', '|detectlanguage', 'test.com']
    if not value: return value
    import re, requests
    from django.conf import settings
    domains = re.findall('https?://(\S+)', value)
    dic = {}
    output = ""
    for domain in domains:
        if not domain[1].lower() in escaped_domains:
            url = 'https://' + domain[1]
            if not url.lower().startswith(settings.BASE_URL):
                try:
                    response = requests.head('https://' + domain[1], timeout=10)
                    if response.status_code == 200:
                        dic[domain[1]] = 'https://' + domain[1]
                except:
                    print("URL does not exist")
            else:
                dic[domain[1]] = 'https://' + domain[1]
    replaced_items = []
    for i, j in dic.items():
        if not i in replaced_items:
            value = value.replace(i, j)
        replaced_items.append(i);
    value = str(value)
    while value.find('https://https://') > -1:
        value = value.replace('https://https://','https://')
    return value

@register.filter(name='removehttps')
def removehttps(value):
    import re
    if not value: return value
    domains = re.findall(r'((https?):\/\/)', value) # '\s(?:www.)?(\w+.(com|org|net|markets))', value)
    dic = {}
    for domain in domains:
        dic[domain[0]] = '' # 'https://' + domain[0]
    for i, j in dic.items():
        value = value.replace(i, j)
    return value

@register.filter(name='embedlinks')
def embedlinks(value):
    from django.conf import settings
    import requests
    if not value: return value
    from urlextract import URLExtract
    extractor = URLExtract()
    lang = ''
    try:
        lang = get_lang()
    except:
        lang = 'en'
    output = ""
    chunks = value.split("https://")
    for x, chunk in enumerate(chunks):
        if x != 0:
            chunk = "https://" + chunk
        urls = extractor.find_urls(chunk);
        dic = {}
        for url in urls:
            plus = ' (it\'s on {})'.format(settings.SITE_NAME)
            ex = ''
            if not url[8:17].lower() == settings.DOMAIN.lower():
                plus = ' (it will take you outside of {})'.format(settings.SITE_NAME)
                ex = ' id=\"external-link\"'
            if url.endswith('.') or url.endswith(',') or url.endswith('!'):
                url = url[:-1]
#            print(chunk[chunk.index(url)-1-len(url)])
#            print(chunk.index(url))
            if chunk[chunk.index(url)-1] == '\"': # or (chunk.index(url) > len(url)-1 and chunk[chunk.index(url)-1-len(url)] == '\"'):
                pass
            elif not url.lower().startswith(settings.BASE_URL) and url.lower().startswith('https://'):
                try:
                    response = requests.head(url, timeout=10)
                    if response.status_code == 200:
                        dic[url] = '<a href=\"' + url + '\" title=\"' + 'Visit this link' + plus + '\"' + ex + '>' + url[8:] + '</a>'
                except:
#                    print("URL does not exist")
                    pass
            elif url.startswith('https://'):
                dic[url] = '<a href=\"' + url + '\" title=\"' + 'Visit this link' + plus + '\">' + url[8:] + '</a>'
        for i, j in dic.items():
            chunk = chunk.replace(i, j)
        output = output + chunk
    return output

@register.filter(name='tagusers')
def tagusers(value):
    import re
    if not value: return value
    lang = ''
    try:
        lang = get_lang()
    except:
        lang = 'en'
    from django.contrib.auth.models import User
    from users.models import Profile
    usernames = re.findall(r"@\s?\w+", value)
    for username in usernames:
        user = username[1:]
        extra = ""
        if user[0:1] == " ":
            extra = " "
            user = user[1:]
        start = 0
        if len(user) > 20:
            start = len(user) - 20
        u = None
        us = None
        p = None
        ps = None
        for x in range(start,len(user)-2):
            n = user[0:len(user)-x]
            try:
                u = User.objects.filter(username__icontains=n, username__length__gt=len(n)-1, username__length__lt=len(n)+4).order_by('-date_joined').first()
                us = User.history.filter(username__icontains=n, username__length__gt=len(n)-1, username__length__lt=len(n)+4).order_by('-date_joined').first()
                p = Profile.objects.filter(name__icontains=n, name__length__gt=len(n)-1, name__length__lt=len(n)+4).order_by('-date_joined').first()
                ps = Profile.history.filter(name__icontains=n, name__length__gt=len(n)-1, name__length__lt=len(n)+4).order_by('-date_joined').first()
            except:
                import traceback
                print(traceback.format_exc())
            if u or us or p or ps:
                break
        if u or us or p or ps:
            u = u if u else us if us else p if p else ps
            from django.urls import reverse
            value = value.replace('@' + extra + u.profile.name, '<a href=\"'+ reverse('feed:profile-grid', kwargs={'username': u.profile.name}) + '\" title=\"' + 'See' + ' @' + u.profile.name + '\'s ' + 'profile' + '\">' + '@' + u.profile.name + '</a>')
    return value

@register.filter(name='filetype')
def filetype(value):
    return value.split('.')[-1].lower()

@register.filter(name='userlikes')
def userlikes(value):
    from feed.models import Post
    from django.contrib.auth.models import User
    pk = int(value)
    post = Post.objects.get(pk=pk)
    if user in post.likes.all():
        return True
    return False

@register.filter(name='postviews')
def postviews(value):
    from feed.models import Post
    post = Post.objects.get(pk=int(value))
    return post.views.count()

@register.filter(name='viewername')
def viewername(value):
    from django.contrib.auth.models import User
    pk = int(value)
    user = User.objects.get(pk=pk)
    return '@' + str(user.username)

@register.filter(name='postcount')
def postcount(value):
    from feed.models import Post
    return str(Post.objects.filter(topic=value).count())

@register.filter(name='commentcount')
def commentcount(value):
    from feed.models import Post
    post = Post.objects.get(id=int(value))
    return False
#    return int(Comment.objects.filter(post=post, public=True).count())

def clean_html(html):
    if html == '': return html
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator="\n")
#        print(text)
        return text.replace('\n\n', '\n')
    except:
        import traceback
        print(traceback.format_exc())
        return html

@register.filter(name='clean')
def clean(text):
    if not text: return ''
    try:
        return str(clean_html(text))
    except: return text

@register.filter(name='shorttitle')
def shorttitle(value):
    from feed.models import Post
    post = Post.objects.get(id=int(value))
    pagetitle = ''
    post.content = clean_html(post.content)
    if len(post.content.splitlines()) > 0:
        pagetitle = post.content.splitlines()[0][0:70]
        if len(post.content.splitlines()[0]) > 70:
            pagetitle = post.content.splitlines()[0][0:67].rsplit(' ', 1)[0] + '...'
    return pagetitle

@register.filter(name='shortdescription')
def shortdescription(value):
    from feed.models import Post
    post = Post.objects.get(id=int(value))
    pagetitle = ''
    description = ''
    post.content = clean_html(post.content)
    if len(post.content.splitlines()) > 0:
        pagetitle = post.content.splitlines()[0][0:70]
        if len(post.content.splitlines()[0]) > 70:
            pagetitle = post.content.splitlines()[0][0:67].rsplit(' ', 1)[0] + '...'
        title = post.content.splitlines()[0][0:30]
        if len(post.content.splitlines()[0]) > 30:
            title = post.content.splitlines()[0][0:30].rsplit(' ', 1)[0] + '...'
        title = 'View Post - \"' + title + '\"'
    if len(post.content.splitlines()) > 1:
        description = post.content.splitlines()[1][0:155]
        if len(description) == 0 and len(post.content.splitlines()) > 2:
            description = post.content.splitlines()[2][0:155]
        if len(description) > 152:
            description = description.rsplit(' ', 1)[0] + '...'
    if description == 'x':
        description = pagetitle
    if description == '':
        description = 'No description for this post.'
    return description


@register.filter(name='geturl')
def geturl(value):
    import re
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', value)
    if not len(urls) > 0:
        return ""
    return urls[0]

@register.filter(name='div2')
def div2(value):
    import math
    return int(math.floor(value/2.0))

@register.filter(name='idscanprice')
def idscanprice(value):
    import math
    return int(math.floor(int(value) * 2.0))

@register.filter(name='striptags')
def striptags(value):
    return strip_tags(value)

@register.filter(name='trimbio')
def trimbio(value):
    from django.utils.html import strip_tags
    value = strip_tags(value)
    if len(value) > 120:
        return value[0:120].rsplit(' ', 1)[0] + '...'
    return value

@register.filter(name='casttofloat')
def casttofloat(thefloat):
    return float(thefloat)

@register.filter(name='highlightcode')
def highlightcode(value):
    import html, re
    from django.conf import settings
    if not value: return value
    if not settings.USE_PRISM: return value
    op = []
    v = value.replace('‘','\'').replace('’','\'').split('***')
    for t in v:
        split = re.split('\*[\w\.]+\*', t)
        language = '\n'
        try:
            language = t[len(split[0]):len(t)-len(split[1])][1:-1].lower()
        except: pass
        if language == 'html': language = 'markup'
        code = split[1] if len(split) > 1 else False
        if code:
            op = op + [{'text': split[0], 'lang': language, 'code': html.escape(code) if language != 'markup' else '<!-- {} -->'.format(code)}]
#            op = op + [language,]'<pre><code class="language-{}">'.format(language if language != 'html' else 'markup') + '{% autoescape on %}' + code + '{% endautoescape %}</code></pre>'
        else:
            op = op + [{'text': split[0]}]
    return op

@register.filter(name='marksafe')
def marksafe(value):
    import html
    from django.utils.html import mark_safe
    return mark_safe(html.unescape(value))

@register.filter(name='caps')
def caps(input):
    return str(input).capitalize()

@register.tag
def linebreakless(parser, token):
    nodelist = parser.parse(('endlinebreakless',))
    parser.delete_first_token()
    return LinebreaklessNode(nodelist)

from django.template.base import Node

class LinebreaklessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        from django.utils.functional import keep_lazy
        import six
        strip_line_breaks = keep_lazy(six.text_type)(lambda x: x.replace('\n', ''))
        return strip_line_breaks(self.nodelist.render(context).strip())

@register.filter('isoformat')
def isoformat(thetime):
    thetime.isoformat()

@register.filter('cryptoformat')
def cryptoformat(amount):
    from django.conf import settings
    return format(float(amount), '.{}f'.format(settings.BITCOIN_DECIMALS))

@register.filter('replspace')
def replspace(text):
    return str(text).replace(' ', '+')

@register.filter('toint')
def toint(text):
    try:
        return int(text)
    except: return 0

@register.filter('scoretotal')
def scoretotal(player):
    total = 0
    for game in player.created_games.all():
        try:
            total = total + int(game.player1_score)
        except: pass
    for game in player.joined_games.all():
        try:
            total = total + (game.player2_score)
        except: pass
    return total

@register.filter('fixalph')
def fixalph(currency):
    if currency == 'ALPH': return 'ETH'
    return currency


def hex_to_hls(hex_color):
    """Converts a hex color to HLS (Hue, Lightness, Saturation)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    import colorsys
    return colorsys.rgb_to_hls(r, g, b)

def get_lightness(hex_color):
  """Gets the lightness of a hex color."""
  return hex_to_hls(hex_color)[1]

@register.filter('blendbright')
def blendbright(color):
    from django.conf import settings
    return get_lightness(color) > get_lightness(settings.BACKGROUND_COLOR) - 0.3

@register.filter('blenddark')
def blenddark(color):
    from django.conf import settings
    return get_lightness(color) < get_lightness(settings.BACKGROUND_COLOR_DARK) + 0.3
