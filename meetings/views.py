from django.shortcuts import render, redirect, get_object_or_404
from .models import Meeting
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified
from django.contrib.auth.decorators import login_required

#@cache_page(60*60*24)
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def schedule_meeting(request):
    import datetime
    from events.models import Event
    from events.forms import EventForm
    from django.utils import timezone
    import pytz
    from django.conf import settings
    form = EventForm(initial={'event_start_date': timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%d"), 'event_start_time': timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%H:%M:00"), 'event_end_date': (timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) + datetime.timedelta(hours=1)).strftime("%Y-%m-%d"), 'event_end_time': (timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) + datetime.timedelta(hours=1)).strftime("%H:%M:00")})
    if request.method == 'POST':
        form = EventForm(request.POST)
        from django.contrib import messages
        if form.is_valid():
            event = form.save()
            try:
                event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M:%S.%f').time())
            except:
                try:
                    event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M:%S').time())
                except:
                    try:
                        event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M').time())
                    except: event.start_time = timezone.now()
            try:
                event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M:%S.%f').time())
            except:
                try:
                    event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M:%S').time())
                except:
                    try:
                        event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M').time())
                    except: event.end_time = timezone.now()
            event.save()
            event.update_description_link(request.user)
            event.notify_scheduled()
            messages.success(request, 'This event has been scheduled and all participants have been informed.')
            from django.urls import reverse
            return redirect(reverse('/'))
        else:
            messages.warning(request, 'This event could not be saved with the following errors: {}'.format(str(form.errors)))
    return render(request, 'meetings/schedule.html', {'title': 'Schedule virtual meeting', 'form': form, 'small': True})

def meeting(request, meeting_id=None):
    """
    Render the meeting page with the specified meeting_id.
    If no meeting_id is provided, create a new Meeting and redirect.
    """
    if not meeting_id:
        meeting = Meeting.objects.create(created_by=request.user)
        return redirect('meetings:meeting', meeting_id=str(meeting.identifier))

    meeting = get_object_or_404(Meeting, identifier=meeting_id)
    # You can use request.user.username if authenticated, else generate a random user ID
    import uuid
    user_id = request.user.id if request.user.is_authenticated else str(uuid.uuid4())[:8]
    return render(request, "meetings/meeting.html", {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "full": True,
    })
