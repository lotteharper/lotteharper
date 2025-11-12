from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    name = forms.CharField(required=False)
    email = forms.EmailField()
    phone = forms.CharField(required=False)
    class Meta:
        model = Contact
        fields = ('name', 'email', 'phone', 'message')

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, *kwargs)
        from feed.middleware import get_current_request
        from translate.translate import translate
        request = get_current_request()
        print(request)
        print(str(request))
        self.fields['name'].label = translate(request, 'Your name', src='en')
        self.fields['email'].label = translate(request, 'Your email address', src='en')
        self.fields['phone'].label = translate(request, 'Your phone number', src='en')
        self.fields['message'].label = translate(request, 'Your message', src='en')
