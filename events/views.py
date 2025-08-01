def add_to_calendar(request, event_id):
    from django.http import HttpResponse
    from icalendar import Calendar, Event as ICalEvent
    from .models import Event
    event = Event.objects.get(identifier=event_id)

    cal = Calendar()
    cal.add('prodid', '-//My Django Events//example.com//')
    cal.add('version', '2.0')

    ical_event = ICalEvent()
    ical_event.add('summary', event.title)
    ical_event.add('dtstart', event.start_time)
    ical_event.add('dtend', event.end_time)
    ical_event.add('description', event.description)
    ical_event.add('location', event.location)

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{event.title.replace(" ", "_")}.ics"'
    return response
