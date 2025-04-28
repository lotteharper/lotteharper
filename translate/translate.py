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
    count = 0
    if target == None and not request.GET.get('lang', None): target = request.LANGUAGE_CODE
    elif target == None and request.GET.get('lang', None): target = request.GET.get('lang', None)
    def thread(target, src, to_trans, count, result):
        translated = translate(None, to_trans, target=target, src=src)
        result[count] = translated
        return
    SIMULTANEOUS_THREADS = 1000
    result_soup = []
    for tag in soup.find_all(string=True):
        if tag.parent.name not in ['script', 'style', 'pre', 'code']:
            result_soup += [tag.string]
        elif tag.parent.name in ['pre', 'code']:
            lines = []
            for line in tag.string.split('\n'):
                if len(line.rsplit('#', 1)) > 1:
                    to_trans = line.rsplit('#', 1)[1]
                    result_soup += [to_trans]
    if not src:
        src = settings.DEFAULT_LANG
        try:
            src = detect(result_soup[0]) if result_soup[0] else settings.DEFAULT_LANG
            langs = detect_langs(result_soup[0]) if result_soup[0] else [settings.DEFAULT_LANG]
            for item in langs:
                if item.lang.startswith(settings.DEFAULT_LANG):
                    src = settings.DEFAULT_LANG
                    break
        except: src = settings.DEFAULT_LANG
    if target and src and target.lower() == src.lower(): return html
    if len(soup.find_all(string=True)) < 1:
        return translate(request, html, target=target, src=src)
    threads = [None] * len(result_soup)
    result = [None] * len(result_soup)
    thread_count = 0
    import threading
    result_arr = [None] * len(result_soup)
    while thread_count < len(result_soup):
        for i in range(SIMULTANEOUS_THREADS):
            if thread_count < len(result_soup):
                threads[thread_count] = threading.Thread(target=thread, args=(target, src, result_soup[thread_count], thread_count, result_arr))
                threads[thread_count].start()
                thread_count += 1
        for i in range(len(threads)):
            if threads[i]: threads[i].join()
    count = 0
    for tag in soup.find_all(string=True):
        if tag.parent.name not in ['script', 'style', 'pre', 'code']:
            tag.replace_with(result_arr[count])
            count+=1
        elif tag.parent.name in ['pre', 'code']:
            lines = []
            for line in tag.string.split('\n'):
                if len(line.rsplit('#', 1)) > 1:
                    to_trans = line.rsplit('#', 1)[1]
                    translated = result_arr[count]
                    line_string = line.rsplit('#', 1)[0] + '# ' + translated
                    lines += [line_string]
                    count+=1
            try:
                if lines: tag.replace_with('\n'.join(lines))
            except: pass
    return str(soup)
