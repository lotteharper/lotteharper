from django import forms
from .models import Event
import datetime

class EventForm(forms.ModelForm):
    event_start_date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(attrs={'type': 'date'})) #auto_now=True, auto_now_add=True)
    event_start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'format': '%H:%M'}))
    event_end_date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(attrs={'type': 'date'})) #auto_now=True, auto_now_add=True)
    event_end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'format': '%H:%M'}))

    def __init__(self, *args, **kwargs):
        from translate.translate import translate
        from feed.middleware import get_current_request
        request = get_current_request()
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['title'].label = translate(request, 'Event Title', src='en')
        self.fields['event_start_date'].label = translate(request, 'Start date', src='en')
        self.fields['event_start_time'].label = translate(request, 'Start time', src='en')
        self.fields['event_end_date'].label = translate(request, 'End date', src='en')
        self.fields['event_end_time'].label = translate(request, 'End time', src='en')
        self.fields['description'].label = translate(request, 'Event description', src='en')
        self.fields['location'].label = translate(request, 'Event location', src='en')
        self.fields['participants'].label = translate(request, 'All participant emails to notify, comma seperated', src='en')
        self.fields['location'].required = False

    class Meta:
        model = Event
        fields = ('title', 'event_start_date', 'event_start_time', 'event_end_date', 'event_end_time', 'description', 'location', 'participants',)
