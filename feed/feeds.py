def get_post_feeds():
    from feed.models import Post
    return Post.objects.values_list('feed', flat=True).distinct()
