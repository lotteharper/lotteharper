def post_ai_response(user, text):
    from feed.models import Post
    from django.conf import settings
    post, created = Post.objects.get_or_create(posted=True, published=True, public=True, private=False, feed=settings.VOICE_FEED, author=user, content=text)
    post.save()

def get_ai_response(text, lang):
    from translate.translate import translate_html
    from django.conf import settings
    lego = translate_html(None, text, src=lang, target=settings.DEFAULT_LANG)
    from openai import OpenAI
    from django.conf import settings
    client = OpenAI(api_key=settings.OPENAI_KEY)
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": lego}
        ]
    )
    return completion.choices[0].message.content
