from django.db import models
from django.utils import timezone
import uuid
from meetings.models import Meeting

def get_event_path(instance, filename):
    import uuid, os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % ('{}'.format(uuid.uuid4()), ext)
    return os.path.join('events/', filename)

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
    image = models.ImageField(upload_to=get_event_path, null=True, blank=True)

    def get_calendar_url(self):
        from django.conf import settings
        from django.urls import reverse
        return settings.BASE_URL + reverse('events:add-to-calendar', kwargs={'event_id': self.identifier})

    def __str__(self):
        return self.title

    def update_description_link(self, creator):
        import uuid
        from django.conf import settings
        from django.urls import reverse
        from meetings.models import Meeting
        self.meeting = Meeting.objects.create(identifier=uuid.uuid4(), created_by=creator)
        self.link = settings.BASE_URL + reverse('meetings:meeting', kwargs={'meeting_id': str(self.meeting.identifier)})
        self.save()
        from events.qrcode import generate_event_qrcode
        generate_event_qrcode(self)
        self.description = self.description + '\n*** Click the link below to start your meeting\n' + self.link + '\nAlternatively, open this code and scan it with your smartphone camera app.\n' + settings.BASE_URL + self.image.url
        self.save()

    def notify_scheduled(self):
        from meetings.email import send_meeting_email
        send_meeting_email(self)
