from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django_recaptcha.fields import ReCaptchaField
from feed.middleware import get_current_request
from django.conf import settings
from feed.templatetags.nts import number_to_string
from dateutil.relativedelta import relativedelta
import datetime
from django.contrib.auth import password_validation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from translate.translate import translate

def get_past_date():
    return datetime.datetime.now() - relativedelta(years=settings.MIN_AGE)

class UserRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    birthday = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    in_agreement = forms.BooleanField(required=True)
    of_age = forms.BooleanField(required=True)
    captcha = ReCaptchaField()

    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        from translate.translate import translate
        from feed.middleware import get_current_request
        r = get_current_request()
        self.fields['password2'].error_messages['password_mismatch'] = translate(r, 'The two password fields didn\'t match.', src='en')
        self.fields['birthday'].initial = get_past_date()
        self.fields['password1'].help_text = translate(r, password_validation.password_validators_help_text_html(), src='en')
        self.fields['password2'].help_text = translate(r, "Enter the same password as before, for verification.", src='en')
        self.fields['in_agreement'].label = translate(r, mark_safe('By checking this box, you are agreeing to the') + ' <a href="/terms/" title="Read the terms of service and privacy policy">Terms of Service and Privacy Policy</a>.')
        self.fields['of_age'].label = translate(r, 'By checking this box, you confirm that you are older than ') + '{} ({})'.format(number_to_string(settings.MIN_AGE), settings.MIN_AGE) + translate(get_current_request(), ' years of age, born on or before {}.'.format(get_past_date().strftime("%B %d, %Y")))
        self.fields['username'].label = translate(r, 'Your username', src='en')
        self.fields['email'].label = translate(r, 'Enter your email', src='en')
        self.fields['password1'].label = translate(r, 'Please enter a password for your account', src='en')
        self.fields['password2'].label = translate(r, 'Enter the same password, for verification', src='en')
        self.fields['captcha'].label = translate(r, 'Please fill out this field to verify you are human', src='en')

    error_messages = {
        'password_mismatch': 'The entered passwords do not match.'
    }


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username', 'email']

phone_number_label = 'Phone number (no spaces, parenthesis \'(\' or dashes \'-\', numbers beginning with + only)'

class NonVendorProfileUpdateForm(forms.ModelForm):
    subscribed = forms.BooleanField(required=False)
    phone_number = forms.CharField(required=False)
    def __init__(self, *args, **kwargs):
        super(NonVendorProfileUpdateForm, self).__init__(*args, **kwargs)
        r = get_current_request()
        from translate.translate import translate
        self.fields['phone_number'].label = translate(r, phone_number_label)
        self.fields['subscribed'].label = translate(r, "Subscribe (uncheck to unsubscribe)")
        self.fields['preferred_name'].label = translate(r, 'Your preferred name', src='en')
        self.fields['name'].label = translate(r, 'Your display name', src='en')
        if self.instance.subscribed:
            self.fields['subscribed'].initial = True
        if self.instance.enable_two_factor_authentication and not settings.ENFORCE_TFA:
            self.fields['enable_two_factor_authentication'].initial = True

    def clean_name(self):
        data = self.cleaned_data['name']
        max_length = 50
        if len(data) > max_length:
            data = data[:max_length]
        return data

    def clean_preferred_name(self):
        data = self.cleaned_data['preferred_name']
        max_length = 50
        if len(data) > max_length:
            data = data[:max_length]
        return data

    class Meta:
        model = Profile
        fields = ['phone_number','enable_two_factor_authentication' if not settings.ENFORCE_TFA else 'phone_number', 'subscribed', 'preferred_name', 'name']


class ProfileUpdateForm(forms.ModelForm):
    subscribed = forms.BooleanField(required=False, label="Subscribe (uncheck to unsubscribe)")
    phone_number = forms.RegexField(regex=r'^\+?1?\d{9,15}$', error_messages = {'invalid': "Phone number must be entered in the format: '+999999999'. Up to 15 digits is allowed."})
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        from translate.translate import translate
        r = get_current_request()
        if self.instance.subscribed:
            self.fields['subscribed'].initial = True
        self.fields['subscribed'].label = translate(r, 'Subscribe to emails?', src='en')
        self.fields['enable_facial_recognition_bypass'].label = translate(r, 'Enable facial recognition bypass?', src='en')
        self.fields['status'].label = translate(r, 'A status text for your fans', src='en')
        self.fields['wishlist'].label = translate(r, 'Your amazon (or other) wishlist', src='en')
        self.fields['bio'].label = translate(r, 'Your bio', src='en')
        self.fields['shop_url'].label = translate(r, 'Your shop url', src='en')
        self.fields['preferred_name'].label = translate(r, 'Preferred name', src='en')
        self.fields['name'].label = translate(r, 'Your display name for your page URL', src='en')
#        self.fields['enable_two_factor_authentication'].label = translate(r, 'Enable two factor authentication?', src='en')
        self.fields['hide_logo'].label = translate(r, 'Hide our logo and brand?', src='en')
        self.fields['image'].label = translate(r, 'Your photo for your page', src='en')
        self.fields['cover_image'].label = translate(r, 'Your cover image', src='en')
        self.fields['bash'].label = translate(r, 'Email username', src='en')
        self.fields['email_password'].label = translate(r, 'Email password', src='en')
        self.fields['shake_to_logout'].label = translate(r, 'Shake to logout?', src='en')
#        self.fields['enable_two_factor_authentication'].label = translate(r, 'Enable two factor authentication', src='en')
        self.fields['phone_number'].label = translate(r, phone_number_label, src='en')
        self.fields['hide_logo'].initial = self.instance.hide_logo
        self.fields['email_password'].initial = ''
        self.fields['email_password'].widget.attrs.update({'placeholder': translate(r, 'Enter to change', src='en'), 'placeholder': translate(r, 'Enter to change', src='en'), })
        self.fields['image'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['cover_image'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['email_password'].help_text = translate(r, 'Please fill in this field to change your email password.', src='en')

    def clean_name(self):
        data = self.cleaned_data['name']
        max_length = 50
        if len(data) > max_length:
            data = data[:max_length]
        return data

    def clean_preferred_name(self):
        data = self.cleaned_data['preferred_name']
        max_length = 50
        if len(data) > max_length:
            data = data[:max_length]
        return data

    class Meta:
        model = Profile
        fields = ['shake_to_logout', 'hide_logo', 'phone_number', 'enable_facial_recognition_bypass', 'enable_biometrics', 'image', 'cover_image', 'bio', 'subscribed', 'status', 'wishlist', 'shop_url', 'preferred_name', 'name', 'bash', 'email_password']
        widgets = {
            'status': forms.Textarea(attrs={'rows':3}),
            'bio': forms.Textarea(attrs={'rows':5}),
            'wishlist': forms.TextInput,
            'shop_url': forms.TextInput,
        }

class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(required=True)

class PhoneNumberForm(forms.Form):
    phone_number = forms.RegexField(regex=r'^\+?1?\d{9,15}$', error_messages = {'invalid': "Phone number must be entered in the format: '+999999999'. Up to 15 digits is allowed."})
    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        from translate.translate import translate
        r = get_current_request()
        self.fields['phone_number'].label = translate(r, phone_number_label, src='en')

class TfaForm(forms.Form):
    send_email = forms.BooleanField(required=False)
    code = forms.IntegerField(required=False)
    def __init__(self, *args, **kwargs):
        super(TfaForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        from translate.translate import translate
        r = get_current_request()
        self.fields['code'].widget.attrs.update({'autocomplete': 'off'})
        self.fields['send_email'].initial = True
        self.fields['send_email'].label = translate(r, 'Send email?', src='en')
        self.fields['code'].label = translate(r, 'Your code', src='en')
        self.fields['code'].help_text = translate(r, 'Please enter the six digit code after sending it to your phone or email with the button above.', src='en')

class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)
        from translate.translate import translate
        from feed.middleware import get_current_request
        r = get_current_request()
        self.fields['new_password2'].error_messages['password_mismatch'] = translate(r, 'The two password fields do not match.', src='en')
        self.fields['new_password1'].label = translate(r, 'New password', src='en')
        self.fields['new_password2'].label = translate(r, 'New password confirmation', src='en')

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

    error_messages = {
        'password_mismatch': 'The entered passwords do not match.'
    }
