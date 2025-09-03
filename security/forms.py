from users.models import Profile
import datetime
from django import forms
from .models import MRZScan, NFCScan, VivoKeyScan

class OTPForm(forms.Form):
    otp = forms.IntegerField(required=True)
    def __init__(self, *args, **kwargs):
        super(OTPForm, self).__init__(*args, **kwargs)
        self.fields['otp'].label = 'One time passcode'

class MRZScanForm(forms.ModelForm):
    class Meta:
        model = MRZScan
        fields = ('image',)

class NFCScanForm(forms.ModelForm):
    class Meta:
        model = NFCScan
        fields = ('nfc_id', 'nfc_data_read', 'nfc_data_written')

class VivoKeyScanForm(forms.ModelForm):
    class Meta:
        model = VivoKeyScan
        fields = ('nfc_id', 'nfc_data_read', 'nfc_data_written')

class PincodeForm(forms.Form):
    pin = forms.IntegerField(required=True)
    def __init__(self, *args, **kwargs):
        super(PincodeForm, self).__init__(*args, **kwargs)
        self.fields['pin'].widget.attrs.update({'autofocus': 'autofocus', 'autocomplete': 'off'})
