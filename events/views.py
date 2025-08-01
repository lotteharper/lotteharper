def strip_non_alpha(text):
    import re
    return re.sub(r'[^a-zA-Z0-9 ]', '', text)

def strip_fix(text):
    import re
    return re.sub(r'[^a-zA-Z0-9,\-:; \'\"()/\\]', '', text)

def add_to_calendar(request, event_id):
    from django.http import HttpResponse
    from icalendar import Calendar, vText, vUri
    from icalendar import Event as ICalEvent
    from .models import Event
    from django.conf import settings
    event = Event.objects.get(identifier=event_id)
    cal = Calendar()
    cal.add('prodid', '-//{} Events//{}//'.format(settings.SITE_NAME, settings.DOMAIN))
    cal.add('version', '2.0')

    ical_event = ICalEvent()
    ical_event.add('summary', strip_fix(event.title))
    ical_event.add('dtstart', event.start_time)
    ical_event.add('dtend', event.end_time)
    ical_event.add('description', event.description) #strip_non_alpha(event.description.rsplit('***', 1)[1]) + '***' + event.description.rsplit('***', 1)[0])
    ical_event.add('location', strip_fix(event.location))
    import base64
    with open(event.image.path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    ical_event.add('attach', vUri(settings.BASE_URL + event.image.url))
#    ical_event.add('attach', vText(f'data:image/png;base64,{image_data}'), parameters={'FILENAME': '{}.png'.format(strip_non_alpha(event.title))})

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{event.title.replace(" ", "_")}.ics"'
    return response
