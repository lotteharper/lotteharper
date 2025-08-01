from django.db import models
from django.utils import timezone
import uuid
from meetings.models import Meeting

class Event(models.Model):
    title = models.CharField(max_length=200)
    identifier = models.CharField(max_length=255, default=uuid.uuid4)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    participants = models.CharField(max_length=1000)
    link = models.CharField(max_length=255)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    def __str__(self):
        return self.title

    def update_description_link(self, creator):
        import uuid
        from django.conf import settings
        from django.urls import reverse
        from meetings.models import Meeting
        self.meeting = Meeting.objects.create(identifier=uuid.uuid4(), created_by=creator)
        self.link = settings.BASE_URL + reverse('meetings:meeting', kwargs={'meeting_id': str(self.meeting.identifier)})
        self.description = self.description + '\n*** Click the link below to start your meeting\n' + self.link
        self.save()

    def notify_scheduled(self):
        from users.email import send_email
        from django.urls import reverse
        from django.conf import settings
        link = settings.BASE_URL + reverse('events:add-to-calendar', kwargs={'event_id': self.identifier})
        participants = self.participants.replace(' ','')
        import pytz
        from django.contrib.auth.models import User
        for email in self.participants.split(','):
            u = User.objects.filter(email=email).order_by('-profile__last_seen').first()
            send_email(email, 'You have been scheduled by {} to join a video meeting with {}'.format(self., 'Hello {},\nYou have been scheduled to join a video meeting with {} {}'.format(settings.SITE_NAME), 'Please click the link below download the attached invite and add it to your calendar for reference by opening it on your device.\n\n<a href="{}">{}</a>\n\nThe invite contains a link to a video meeting. Please click the link in the description of the invite in your calendar and join the meeting from your phone, tablet, or other device.\nWhen the meeting starts, please click the link below or the link in the invite.\n\n<a href="{}">{}</a>'.format('' if not u else u.profile.name, link, link, self.start_time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%m/%d/%Y at %H:%M:%S'), self.link, self.link))
