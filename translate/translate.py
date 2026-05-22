import asyncio
from django.conf import settings
import traceback
from langdetect import detect, detect_langs
from googletrans import Translator
from translate.languages import SELECTOR_LANGUAGES

MAX_TRANS = 5000
TRANSLATION_CACHE_TIMEOUT = 60*60*24*30*12
SIMULTANEOUS_THREADS = 100

def unbatch_strings(strings, max_len=4000, sep="\n|||TRANS|||\\n"):
    res = []
    for string in strings:
        res += string.split(sep)
    return res

def batch_strings(strings, max_len=4000, sep="\n|||TRANS|||\\n"):
    batches = []
    current = []
    current_len = 0

    for s in strings:
        extra = len(s) + (len(sep) if current else 0)
        if current and current_len + extra > max_len:
            batches.append(current)
            current = [s]
            current_len = len(s)
        else:
            current.append(s)
            current_len += extra

    if current:
        batches.append(current)
    return batches

def split_text_by_length(text, max_len=MAX_TRANS):
    words = text.split()
    parts = []
    curr_part = []
    for word in words:
        tentative = ' '.join(curr_part + [word]) if curr_part else word
        if len(tentative) > max_len:
            # Finish current part and start a new one with current word
            if curr_part:
                parts.append(' '.join(curr_part))
            curr_part = [word]
        else:
            curr_part.append(word)
    if curr_part:
        parts.append(' '.join(curr_part))
    return parts

def translate(request, content, target=None, src=None):
    import time
    import hashlib
    from django.core.cache import cache
    global MAX_TRANS
#    from django.core.cache import caches
    global TRANSLATION_CACHE_TIMEOUT
#    cache = caches['translation_cache']
    hash_object = hashlib.md5(content.encode('utf-8'))
    src_hash = hash_object.hexdigest()
    cache_key = f"translation:{src}:{target}:{src_hash}"
    db_key = f"{src}:{target}:{src_hash}"
    if (not content) or content == '' or content == None or (src != None and target != None and target == src): return content
    translation = cache.get(cache_key)
    if translation is not None:
        return translation
    lang = src
    if not src:
        lang = settings.DEFAULT_LANG
#        try:
#            lang = detect(content)
#            langs = detect_langs(content)
#            for item in langs:
#                if item.lang.startswith(settings.DEFAULT_LANG):
#                    lang = settings.DEFAULT_LANG
#                    break
#        except: lang = settings.DEFAULT_LANG
    lang_code = None
    if target:
        lang_code = target
    elif request != None:
        if request and ((request.user.is_authenticated and request.user.profile.preferred_language) or hasattr(request, 'LANGUAGE_CODE')) and not request.GET.get('lang', False):
            lang_code = (request.user.profile.preferred_language if hasattr(request, 'user') and hasattr(request.user, 'profile') and request.user.is_authenticated and request.user.profile.preferred_language else request.LANGUAGE_CODE if not request.GET.get('lang', None) else request.GET.get('lang')) if request != None else settings.DEFAULT_LANG
        else:
            lang_code = (settings.DEFAULT_LANG if (not request) or not request.GET.get('lang', None) else request.GET.get('lang')) if request != None else settings.DEFAULT_LANG
    lang_code = str(lang_code)
    if not lang: lang = settings.DEFAULT_LANG
    if target:
        lang_code = target
    lang_code = lang_code.lower()
    if str(lang_code).startswith(str(lang)) or str(lang_code) == str(lang) or str(lang_code) == src:
        return content
    if (not content) or content == '' or content == None or (src != None and target != None and target == src): return content
    if (not content) or content == '' or content == None or (lang != None and lang_code != None and lang_code == lang): return content
    if not lang_code: return content
    if not src: src = settings.DEFAULT_LANG
    if not lang_code in SELECTOR_LANGUAGES.keys():
        from django.contrib import messages
        if request and 'lang' in list(request.GET.keys()): messages.warning(request, 'You have selected a language not yet available for translation. Please change the "lang=" parameter in the URL to a valid two character language code for Google Translate API such as "en", "es" or "de", or <a href="/" title="Return home and clear the lang parameter for now">click here to return home</a>.')
        return content
    translation = cache.get(cache_key)
    if translation is not None:
        return translation
    from .models import CachedTranslation
    trans = CachedTranslation.objects.filter(src_hash=db_key).order_by('timestamp').first()
    if trans: return trans.dest_content
    text = ''
    pronunciation = ''
    content = content.replace('\n', '<br/>')
    content_fragments = split_text_by_length(content, max_len=MAX_TRANS)
    async def translate_fragments(fragments, src, dest, concurrency=10):
        sem = asyncio.Semaphore(concurrency)
        async with Translator() as translator:
            async def one(i, text):
                async with sem:
                    result = await translator.translate(text, src=src, dest=dest)
                    return i, result.text

            tasks = [one(i, text) for i, text in enumerate(fragments)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    results = asyncio.run(translate_fragments(content_fragments, src, lang_code))
    result_arr = [item[1] for item in results]
    try: translator.client.close()
    except: pass
    translator = None
    result_text = ''
    pronunciation_text = ''
    for x in range(len(result_arr)):
        text = result_arr[x]
        if text:
            if len(result_text) > 0 and result_text[-1:] != ' ': result_text = result_text + ' '
            result_text = result_text + text
    text = result_text.replace('<br/>', '\n')
    pronunciation = pronunciation_text
    if len(text) > 0:
        try:
            CachedTranslation.objects.get_or_create(src_content=content, dest_content=text, src=lang, dest=lang_code, pronunciation=pronunciation, src_hash=db_key)
        except: pass
    else: return content
    cache.set(cache_key, text, timeout=TRANSLATION_CACHE_TIMEOUT)
    return text

def translate_html(request, html, target=None, src=None):
    import time
    import hashlib
    from django.utils.html import strip_tags
    if strip_tags(html) == html: return translate(request, html, target=target, src=src)
    from django.core.cache import cache
#    from django.core.cache import caches
    global TRANSLATION_CACHE_TIMEOUT
#    cache = caches['translation_cache']
    hash_object = hashlib.md5(html.encode('utf-8'))
    src_hash = hash_object.hexdigest()
    cache_key = f"translation:{src}:{target}:{src_hash}"
    db_key = f"{src}:{target}:{src_hash}"
    translation = cache.get(cache_key)
    if translation is not None:
        return translation
    """Translates HTML content to the target language."""
    count = 0
    if target == None and request and not (request.GET.get('lang', None) or (hasattr(request, 'user') and hasattr(request.user, 'profile') and request.user.is_authenticated and request.user.profile.preferred_language)): target = request.LANGUAGE_CODE
    elif target == None and request and ((not request.GET.get('lang', None)) and (hasattr(request, 'user') and hasattr(request.user, 'profile') and request.user.is_authenticated and request.user.profile.preferred_language)):
        target = request.user.profile.preferred_language
    elif target == None and request and request.GET.get('lang', None): target = request.GET.get('lang', None)
    elif not target: target = settings.DEFAULT_LANG
    # Try to get the translation from cache
    if target == src:
        return html
    translation = cache.get(cache_key)
    if translation is not None:
        return translation
    from .models import CachedTranslation
    trans = CachedTranslation.objects.filter(src_hash=db_key).order_by('timestamp').first()
    if trans:
        return trans.dest_content
    async def thread(target, src, to_trans, count, result):
        try:
            if to_trans != None and to_trans != '':
                async with Translator() as translator:
                    trans = await translator.translate(to_trans, src=src, dest=target)
                    result[count] = str(trans.text)
        except:
            print(traceback.format_exc())
            pass
    result_soup = []
    from django.utils.html import strip_tags
    from bs4 import BeautifulSoup, NavigableString
    soup = BeautifulSoup(html, 'html.parser')
    for tag in [tag for tag in soup.find_all(string=True)]:
        if tag.parent.name not in ['script', 'style', 'pre', 'code'] and tag.string:
#            print(strip_tags(str(tag.string)))
            result_soup += [strip_tags(str(tag.string))]
        elif tag.parent.name in ['pre', 'code'] and tag.string:
            lines = []
            for line in tag.string.split('\n'):
                if len(line.rsplit('#', 1)) > 1:
                    to_trans = line.rsplit('#', 1)[1]
                    result_soup += [to_trans]
    for tag in soup.find_all('a'):
        if 'title' in tag.attrs:
            result_soup += [tag['title']]
    for tag in soup.find_all('img'):
        if 'alt' in tag.attrs:
            result_soup += [tag['alt']]
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
    if target and src and target.lower() == src.lower():
        return html
    if len(soup.find_all()) <= 1:
        translation = translate(request, html, target=target, src=src)
        cache.set(cache_key, translation, timeout=TRANSLATION_CACHE_TIMEOUT)
#    print(result_soup)
    async def translate_fragments(fragments, src, dest, concurrency=10):
        sem = asyncio.Semaphore(concurrency)
        async with Translator() as translator:
            async def one(i, text):
                async with sem:
                    result = await translator.translate(text, src=src, dest=dest)
                    return i, result.text

            tasks = [one(i, text) for i, text in enumerate(fragments)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    results = batch_strings(result_soup)[0]
    result = asyncio.run(translate_fragments(results, src, target))
    result_ar = [item[1] for item in result]
    result_arr = unbatch_strings(result_ar)
    count = 0
    for tag in soup.find_all(string=True):
        if tag.parent.name not in ['script', 'style', 'pre', 'code'] and tag.string:
            tag.string.replace_with(result_arr[count] if count < len(result_arr) and result_arr[count] else '')
            count+=1
        elif tag.parent.name in ['pre', 'code'] and tag.string:
            lines = []
            for line in tag.string.split('\n'):
                if len(line.rsplit('#', 1)) > 1:
                    to_trans = line.rsplit('#', 1)[1]
                    translated = result_arr[count] if count < len(result_arr) else None
                    line_string = line.rsplit('#', 1)[0] + '# ' + translated if translated else ''
                    lines += [line_string]
                    count+=1
            try:
                if lines: tag.string.replace_with('\n'.join(lines))
            except: pass
#    print(result_arr)
    for tag in soup.find_all('a'):
        if 'title' in tag.attrs:
            tag['title'] = result_arr[count] if count < len(result_arr) and result_arr[count] else ''
            count+=1
    for tag in soup.find_all('img'):
        if 'alt' in tag.attrs:
            tag['alt'] = result_arr[count] if count < len(result_arr) and result_arr[count] else ''
            count+=1
    result = str(soup).replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
#    print(result)
    if len(result) > 0:
        try:
            CachedTranslation.objects.get_or_create(src_content=html, src_hash=db_key, dest_content=result, src=src, dest=target)
        except: pass
    cache.set(cache_key, result, timeout=TRANSLATION_CACHE_TIMEOUT)
    return result

def translate_multiple(request, split, target=None, src=None):
    import hashlib
    from django.core.cache import cache
#    from django.core.cache import caches
    global TRANSLATION_CACHE_TIMEOUT
#    cache = caches['translation_cache']
    hash_object = hashlib.md5(str(split).encode('utf-8'))
    src_hash = hash_object.hexdigest()
    cache_key = f"translation:{src}:{target}:{src_hash}"
    db_key = f"{src}:{target}:{src_hash}"
    if target == src:
        return split
    translation = cache.get(cache_key)
    if translation is not None:
        return translation
    from .models import CachedTranslation
    trans = CachedTranslation.objects.filter(src_hash=db_key).order_by('timestamp').first()
    if trans:
        return trans.dest_content
    from translate.translate import translate
    from feed.middleware import get_current_request
    from django.conf import settings
    from threading import Thread
    if not request: request = get_current_request()
    if not target:
        target = request.user.profile.preferred_language if hasattr(request, 'user') and hasattr(request.user, 'profile') and not request.GET.get('lang', False) else request.LANGUAGE_CODE if request and not request.GET.get('lang') else request.GET.get('lang') if request and request.GET.get('lang', None) else settings.DEFAULT_LANG
    if not src: src = settings.DEFAULT_LANG
    async def translate_fragments(fragments, src, dest, concurrency=10):
        sem = asyncio.Semaphore(concurrency)
        async with Translator() as translator:
            async def one(i, text):
                async with sem:
                    result = await translator.translate(text, src=src, dest=dest)
                    return i, result.text

            tasks = [one(i, text) for i, text in enumerate(fragments)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    results = batch_strings(split)
    result = asyncio.run(translate_fragments(results, src, target))
    result_ar = [item[1] for item in result]
    result_arr = unbatch_strings(result_ar)
    if len(result_arr) > 0:
        try:
            CachedTranslation.objects.get_or_create(src_content=split, src_hash=db_key, dest_content=str(result), src=src, dest=target)
        except: pass
    cache.set(cache_key, result, timeout=TRANSLATION_CACHE_TIMEOUT)
    return result
