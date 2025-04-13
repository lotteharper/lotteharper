from django.conf import settings
import traceback
from langdetect import detect, detect_langs
from googletrans import Translator

MAX_TRANS = 1000

def translate(request, content, target=None, src=None):
    if (not content) or content == '' or content == None or (src != None and target != None and target == src): return content
    lang = src
    if not src:
        lang = settings.DEFAULT_LANG
        try:
            lang = detect(content)
            langs = detect_langs(content)
            for item in langs:
                if item.lang.startswith(settings.DEFAULT_LANG):
                    lang = settings.DEFAULT_LANG
                    break
        except: lang = settings.DEFAULT_LANG
    lang_code = None
    if target:
        lang_code = target
    elif request != None:
        if hasattr(request, 'LANGUAGE_CODE'):
            lang_code = (request.LANGUAGE_CODE if not request.GET.get('lang', None) else request.GET.get('lang')) if request != None else settings.DEFAULT_LANG
        else:
            lang_code = (settings.DEFAULT_LANG if not request.GET.get('lang', None) else request.GET.get('lang')) if request != None else settings.DEFAULT_LANG
    lang_code = str(lang_code)
    if not lang: lang = settings.DEFAULT_LANG
    if request != None and request.GET.get('lang', False): lang_code = request.GET.get('lang', None)
    if target:
        lang_code = target
    lang_code = lang_code.lower()
    if str(lang_code).startswith(str(lang)) or str(lang_code) == str(lang) or str(lang_code) == src:
        return content
    from .models import CachedTranslation
    trans = CachedTranslation.objects.filter(src_content=content, src=lang, dest=lang_code).order_by('timestamp').first()
    if trans: return trans.dest_content
    text = ''
    pronunciation = ''
    c = ''
    last = False
#    print('Src lang code is ' + lang + ', target is ' + lang_code)
    for x in range(0, int(len(content)/MAX_TRANS) + 1):
        try:
            translator = Translator()
            if len(content) < MAX_TRANS:
                trans = translator.translate(content, src=lang, dest=lang_code)
                text = text + str(trans.text)
                pronunciation = pronunciation + str(trans.pronunciation[0]) if hasattr(trans, 'pronunciation') and trans.pronunciation else ''
                break
            if (x+1) * MAX_TRANS > len(content): last = True
            c = content[x * MAX_TRANS - (0 if not c else MAX_TRANS-len(c)):(x+1)*MAX_TRANS - (0 if not c else MAX_TRANS-len(c) if not last else -1 * MAX_TRANS)].rsplit(' ', 1)[0]
            trans = translator.translate(c, src=lang, dest=lang_code)
            text = text + str(trans.text)
            pronunciation = pronunciation + str(trans.pronunciation[0]) if hasattr(trans, 'pronunciation') and trans.pronunciation else ''
        except:
            print(traceback.format_exc())
            pass
    if len(text) > 0:
        try:
            CachedTranslation.objects.get_or_create(src_content=content, dest_content=text, src=lang, dest=lang_code, pronunciation=pronunciation)
        except: pass
    else: return content
    return text


def translate_html(request, html, target=None, src=None):
    """Translates HTML content to the target language."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(string=True):
        if tag.parent.name not in ['script', 'style', 'pre', 'code']:
            translated = translate(request, tag.string, target=target, src=src)
            tag.replace_with(translated)
        elif tag.parent.name in ['pre', 'code']:
            lines = []
            for line in tag.string.split('\n'):
                if len(line.rsplit('#', 1)) > 1:
                    to_trans = line.rsplit('#', 1)[1]
                    translated = translate(request, to_trans, target=target, src=src)
                    line_string = line.rsplit('#', 1)[0] + '# ' + translated
                else: line_string = line
                lines = lines + [line_string]
            out = '\n'.join(lines)
            tag.replace_with(out)
    return str(soup)
