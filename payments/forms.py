from django import forms
from .models import CustomerPaymentsProfile
from .models import PaymentCard
from address.forms import AddressField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

class CardNumberForm(forms.ModelForm):
    agreed = forms.BooleanField(required=True)
    def __init__(self, user, *args, **kwargs):
        super(CardNumberForm, self).__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.save()
        self.fields['agreed'].label = 'By checking this box, you agree to the <a href="/terms/" title="Read the terms of service and privacy policy">Terms of Service and Privacy Policy</a>, as well as agree to and and acknowledge the sale as outlined.'
        self.fields['address'].required = True
        self.fields['number'].widget.attrs.update({'autocomplete': 'cc-number'})
    class Meta:
        model = PaymentCard
        fields = ('agreed', 'address', 'number',)

expiry_months = ['MM']
for x in range(12):
    val = str(x + 1)
    expiry_months = expiry_months + [[val,val]]

expiry_years = ['YY']
for x in range(10):
    val = str(timezone.now().year + x)[2:]
    expiry_years = expiry_years + [[val,val]]

class CardInfoForm(forms.ModelForm):
    expiry_month = forms.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)]) #forms.CharField(widget=forms.Select(choices=expiry_months),max_length=2)
    expiry_year = forms.IntegerField(validators=[MinValueValidator(timezone.now().year - 2000), MaxValueValidator(timezone.now().year + 10)]) #forms.CharField(widget=forms.Select(choices=expiry_years),max_length=4)
    def __init__(self, user, *args, **kwargs):
        super(CardInfoForm, self).__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.save()
        self.fields['expiry_month'].widget.attrs.update({'autocomplete': 'cc-exp-month'})
        self.fields['expiry_year'].widget.attrs.update({'autocomplete': 'cc-exp-year'})
        self.fields['cvv_code'].widget.attrs.update({'autocomplete': 'cc-csc'})
    class Meta:
        model = PaymentCard
        fields = ('expiry_month','expiry_year','cvv_code',)


CHOICES = [['individual','Individual'], ['business', 'Business']]

class InvoiceForm(forms.Form):
    client_email = forms.EmailField()
    cost = forms.FloatField(required=True)
    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.fields['cost'].initial = 100.0
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['client_email'].label = translate(r, 'The client\'s email for the invoice', src='en')
        self.fields['cost'].label = translate(r, 'The cost of the invoice in USD', src='en')
        self.fields['description'].label = translate(r, 'A description of the product/serivce', src='en')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}))


class PaymentForm(forms.Form):
    total = forms.FloatField(required=True, max_value=1000000000000, min_value=0.99, widget=forms.NumberInput(attrs={'step': "0.01"}))
    item_name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    full_name = forms.CharField(max_length=100)
    customer_type = forms.CharField(widget=forms.Select(choices=CHOICES))

class BitcoinPaymentForm(forms.Form):
    transaction_id = forms.CharField(max_length=100)
    amount = forms.CharField(max_length=100)
    invoice = forms.CharField(max_length=100, required=False)
    email = forms.EmailField()
    def __init__(self, *args, **kwargs):
        super(BitcoinPaymentForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['email'].label = translate(r, 'Your email for the invoice', src='en')
        self.fields['transaction_id'].widget = forms.HiddenInput()
        self.fields['amount'].widget = forms.HiddenInput()
        self.fields['invoice'].widget = forms.HiddenInput()

class BitcoinPaymentFormUser(forms.Form):
    transaction_id = forms.CharField(max_length=100)
    amount = forms.CharField(max_length=100)
    invoice = forms.CharField(required=False, max_length=100)
    def __init__(self, *args, **kwargs):
        super(BitcoinPaymentFormUser, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['transaction_id'].widget = forms.HiddenInput()
        self.fields['amount'].widget = forms.HiddenInput()
        self.fields['invoice'].widget = forms.HiddenInput()

class CardPaymentForm(forms.Form):
    email = forms.EmailField(required=True)
    product = forms.HiddenInput()
    pid = forms.HiddenInput()
    def __init__(self, *args, **kwargs):
        super(CardPaymentForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['email'].label = translate(r, 'Your email for the invoice', src='en')
        from django.conf import settings
        if r.user.is_authenticated or settings.PAYMENT_PROCESSOR == 'stripe':
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False

class TipCryptoForm(forms.Form):
    tip = forms.FloatField(required=True)
    def __init__(self, *args, **kwargs):
        super(TipCryptoForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['tip'].label = translate(r, 'Your tip in USD', src='en')
        self.fields['tip'].initial = 0.0
