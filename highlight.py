import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

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

def highlightsearchquery(text):
    from feed.middleware import get_current_request
    request = get_current_request()
    q = '22LR'
    from django.conf import settings
    from translate.translate import translate
    q = translate(request, q, target=settings.DEFAULT_LANG)
    from misc.sitemap import languages
    threads = [None] * len(languages)
    results = [None] * len(languages)
    thread_count = 0
    def highlight_lang(q, lang, text, results, count):
        from translate.translate import translate
        res = highlight_query(translate(None, q, target=lang), text)
        results[count] = res
    import threading
    for lang in languages:
        threads[thread_count] = threading.Thread(target=highlight_lang, args=(q, lang, text, results, thread_count, ))
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

print(highlightsearchquery('test 22LR test'))

