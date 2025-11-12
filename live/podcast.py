def update_user_podcasts(user):
    page = 1
    results_per_page = 5
    podcasts = get_podcasts(user, page, results_per_page)
    while podcasts:
        print(podcasts)
        for transistorfm_id, title, description, image_url, created_at, explicit, category in podcasts:
            podcasts = user.transistorfm_podcasts.filter(transistorfm_id=int(transistorfm_id))
            if podcasts.count() == 0:
                from live.models import UserPodcast
                podcast = UserPodcast.objects.create(user=user, transistorfm_id=int(transistorfm_id), title=title, description=description, image_url=image_url, created_at=created_at, explicit=explicit, category=category)
            else:
                podcast = podcasts.first()
                podcast.title = title
                podcast.transistorfm_id = int(transistorfm_id)
                podcast.description = description
                podcast.image_url = image_url
                podcast.created_at = created_at
                podcast.explicit = explicit
                podcast.category = category
                podcast.save()
        if len(podcasts) == results_per_page:
            page += 1
            podcasts = get_podcasts(user, page, 5)
        else: podcasts = None

def get_podcasts(user, page, results_per_page):
    from django.conf import settings
    headers = {'x-api-key': user.vendor_profile.transistorfm_key}
    payload = {"pagination": {'page': page, 'per': results_per_page}, "fields": {'show': ['title', 'description']}}
    import requests, json
    resp = requests.get('https://api.transistor.fm/v1/shows', headers=headers, data=json.dumps(payload))
    try:
        data = resp.json()['data']
        from datetime import datetime, timezone
        output = []
        for podcast in data:
            output += [(podcast['id'], podcast['attributes']['title'], podcast['attributes']['description'], podcast['attributes']['image_url'], datetime.strptime(podcast['attributes']['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc), podcast['attributes']['explicit'], podcast['attributes']['category'])]
        return output
    except: return False

def upload_podcast(user, show_id, file_path, episode_number, season_number, title, summary, transcript, image_url=None, explicit=False, video_url=None, keywords=None):
    id, upload_url, audio_url, content_type = authorize_upload(user, file_path)
    from live.models import UserPodcastAudioUpload
    upload = UserPodcastAudioUpload.objects.create(user=user, upload_url=upload_url, audio_url=audio_url, transistorfm_id=id, content_type=content_type)
    import requests, json
    headers = {"Content-Type": "audio/mpeg"}
    with open(file_path, "rb") as f:
        response = requests.put(
            upload_url,
            data=f,
            headers=headers
        )
    episode_id, r = create_episode(user, show_id, episode_number, season_number, title, summary, audio_url, transcript, image_url, explicit=explicit, video_url=video_url, keywords=keywords)
    ret = publish_episode(user, episode_id)
    upload.success_json = json.dumps(r)
    upload.successful = ret and response.status_code == 200
    upload.save()
    return ret

def create_episode(user, show_id, episode_number, season_number, title, summary, audio_url, transcript, image_url, explicit=False, video_url=None, keywords=None):
    headers = {'x-api-key': user.vendor_profile.transistorfm_key, "Content-Type": "application/json"}
    payload = {'episode': {'type': 'full', 'show_id': show_id, 'title': title, 'summary': summary, 'audio_url': audio_url, 'explicit': explicit, 'transcript_text': transcript} }
    if episode_number: payload['episode']['number'] = episode_number
    if season_number: payload['episode']['season'] = season_number
    if video_url: payload['episode']['video_url'] = video_url
    if image_url: payload['episode']['image_url'] = image_url
    if keywords: payload['episode']['keywords'] = keywords
#    payload['episode']['increment_number'] = True
    import requests, json
    response = requests.post('https://api.transistor.fm/v1/episodes', headers=headers, data=json.dumps(payload))
    r = response.json()
    return r['data']['id'], r

def publish_episode(user, episode_id):
    import requests, json
    headers = {'x-api-key': user.vendor_profile.transistorfm_key}
    payload = {'id': episode_id, 'episode[status]': 'published', 'fields[episode][]': 'status'}
    response = requests.patch(f"https://api.transistor.fm/v1/episodes/{episode_id}/publish", headers=headers, data=payload)
    return response.status_code == 200

def authorize_upload(user, path):
    import requests, json
    headers = {'x-api-key': user.vendor_profile.transistorfm_key}
    payload = {'filename': path.rsplit('/', 1)[1]}
    resp = requests.get('https://api.transistor.fm/v1/episodes/authorize_upload', headers=headers, params=payload)
    try:
        data = resp.json()['data']
        return data['id'], data['attributes']['upload_url'], data['attributes']['audio_url'], data['attributes']['content_type']
    except: return False
