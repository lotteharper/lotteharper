def send_meeting_email(event):
    meeting = event.meeting
    from django.urls import reverse
    from django.conf import settings
    participants = event.participants.replace(' ','')
    import pytz
    from django.contrib.auth.models import User
    for email in participants.split(','):
        user = User.objects.filter(email=email).order_by('-profile__last_seen').first()
        context = {
            'username': user.profile.name if user else 'guest',
            'meeting': meeting,
            'calendar_link': event.get_calendar_url(),
            'meeting_link': meeting.get_absolute_url(),
            'site_name': settings.SITE_NAME,
            'start_time': event.start_time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%m/%d/%Y at %H:%M:%S'),
        }
        from django.template.loader import render_to_string
        content = render_to_string('meetings/email.html', context)
        from users.email import send_email
        send_email(email, 'You have been scheduled by {} to join a video meeting online with {}'.format(meeting.created_by.profile.name, settings.SITE_NAME), content)
