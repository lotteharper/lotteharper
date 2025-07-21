from django import forms
import datetime
from .models import Post, Bid, Report
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget
from django.conf import settings
from django.utils import timezone

def sub_fee(fee):
    import math
    op = ''
    of = len(str(fee))%3
    op = op + str(fee)[0:of] + (',' if of > 0 else '')
    for f in range(math.floor(len(str(fee))/3)):
        op = op + str(fee)[3*f+of:3+3*f+of] + ','
    op = op[:-1]
    return op

def get_pricing():
    from lotteh.pricing import get_pricing_options
    choices = []
    for option in get_pricing_options(settings.PHOTO_CHOICES):
        choices = choices + [[option, '${}'.format(sub_fee(option))]]
    return choices

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PostForm(forms.ModelForm):
    private = forms.BooleanField(required=False)
    public = forms.BooleanField(required=False)
    content = forms.CharField(widget=SummernoteInplaceWidget(attrs={'rows': settings.TEXTAREA_ROWS}), required=False)
#    clear_redacted = forms.BooleanField(required=False, widget=forms.HiddenInput)
    recipient = forms.CharField(widget=forms.HiddenInput(), required=False)
    image = MultipleImageField(required=False) #forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True, 'multiple': True}))
    file = MultipleFileField(required=False) #forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True, 'multiple': True}))
    confirmation_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    price = forms.CharField(widget=forms.Select(choices=get_pricing()))

    def __init__(self, *args, **kwargs):
        from feed.middleware import get_current_request
        r = get_current_request()
        super(PostForm, self).__init__(*args, **kwargs)
        if not self.instance: self.fields['price'].initial = r.user.vendor_profile.photo_tip[1:]
        if r.GET.get('raw', None): self.fields['content'].widget = forms.Textarea(attrs={'rows': settings.TEXTAREA_ROWS})
        self.fields['image'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['file'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        if r.GET.get('camera'):
            self.fields['image'].widget.attrs.update({'capture': 'user'})
            self.fields['file'].widget.attrs.update({'accept': 'video/*', 'capture': 'user'})
        if r.GET.get('audio'):
            self.fields['file'].widget.attrs.update({'accept': 'audio/*', 'capture': 'user'})
        from translate.translate import translate
        if self.instance and self.instance.private:
            qs = []
            if self.instance.recipient:
                self.fields['recipient'].initial = str(self.instance.recipient.id)
            qs = qs + [('0', translate(r, 'No recipient', src='en'))]
            for q in self.instance.author.subscriptions.all():
                qs = qs + [(str(q.id), '+ ' + q.name)]
            self.fields['recipient'].widget = forms.Select(choices=qs)
        if self.instance.pk == None:
            self.fields['public'].widget=forms.CheckboxInput(attrs={'checked': True})
        self.fields['feed'].label = translate(r, 'Blog feed', src='en')
        self.fields['content'].label = translate(r, 'Content', src='en')
        self.fields['image'].label = translate(r, 'Upload an image', src='en')
        self.fields['file'].label = translate(r, 'Upload a file', src='en')
        self.fields['price'].label = translate(r, 'Name your price', src='en')
        self.fields['private'].label = translate(r, 'Private?', src='en')
        self.fields['public'].label = translate(r, 'Public?', src='en')
        self.fields['pinned'].label = translate(r, 'Pin post?', src='en')
        self.fields['paid_file'].label = translate(r, 'Paid file?', src='en')

    class Meta:
        model = Post
        fields = ('feed', 'content', 'image', 'file', 'price', 'private', 'public', 'pinned', 'confirmation_id', 'paid_file')

class ScheduledPostForm(forms.ModelForm):
    date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(attrs={'type': 'date'})) #auto_now=True, auto_now_add=True)
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'format': '%H:%M'}))
    image = MultipleImageField(required=False) #forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True, 'multiple': True}))
    file = MultipleFileField(required=False) #forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True, 'multiple': True}))
    content = forms.CharField(widget=SummernoteInplaceWidget(attrs={'rows': settings.TEXTAREA_ROWS}), required=False)
#    clear_redacted = forms.BooleanField(required=False, widget=forms.HiddenInput)
    recipient = forms.CharField(widget=forms.HiddenInput(), required=False)
    confirmation_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    PHOTO_CHOICES = (
        ('5', '$5'),
        ('10', '$10'),
        ('20', '$20'),
        ('25', '$25'),
        ('50', '$50'),
        ('100', '$100'),
    )
    price = forms.CharField(widget=forms.Select(choices=get_pricing()))
    date_auction = forms.DateField(initial=timezone.now() - datetime.timedelta(days=365), widget=forms.DateInput(attrs={'type': 'date'})) #auto_now=True, auto_now_add=True)
    auction_message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def __init__(self, *args, **kwargs):
        from security.crypto import decrypt_cbc
        from django.conf import settings
        from feed.middleware import get_current_request
        r = get_current_request()
        super(ScheduledPostForm, self).__init__(*args, **kwargs)
        if not self.instance: self.fields['price'].initial = r.user.vendor_profile.photo_tip[1:]
        if r.GET.get('raw', None): self.fields['content'].widget = forms.Textarea(attrs={'rows': settings.TEXTAREA_ROWS})
#        self.fields['auction_message'].initial = decrypt_cbc(self.instance.auction_message, settings.AES_KEY)
        self.fields['image'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['file'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        if r.GET.get('camera'):
            self.fields['image'].widget.attrs.update({'capture': 'user'})
            self.fields['file'].widget.attrs.update({'accept': 'video/*', 'capture': 'user'})
        if r.GET.get('audio'):
            self.fields['file'].widget.attrs.update({'accept': 'audio/*', 'capture': 'user'})
        if self.instance and not self.instance.date_auction > timezone.now() - datetime.timedelta(days=365):
            self.fields['auction_message'].widget = forms.HiddenInput()
        from translate.translate import translate
        if self.instance and self.instance.private:
            qs = []
            if self.instance.recipient:
                self.fields['recipient'].initial = str(self.instance.recipient.id)
            qs = qs + [('0', translate(r, 'No recipient', src='en'))]
            for q in self.instance.author.subscriptions.all():
                qs = qs + [(str(q.id), '+ ' + q.name)]
            self.fields['recipient'].widget = forms.Select(choices=qs)
        if self.instance.pk == None:
            self.fields['public'].widget=forms.CheckboxInput(attrs={'checked': True})
        self.fields['feed'].label = translate(r, 'Blog feed', src='en')
        self.fields['content'].label = translate(r, 'Content', src='en')
        self.fields['image'].label = translate(r, 'Upload an image', src='en')
        self.fields['file'].label = translate(r, 'Upload a file', src='en')
        self.fields['price'].label = translate(r, 'Name your price', src='en')
        self.fields['private'].label = translate(r, 'Private?', src='en')
        self.fields['public'].label = translate(r, 'Public?', src='en')
        self.fields['pinned'].label = translate(r, 'Pin post?', src='en')
        self.fields['paid_file'].label = translate(r, 'Paid file?', src='en')
        self.fields['date_auction'].label = translate(r, 'Auction date', src='en')

    class Meta:
        model = Post
        fields = ('feed', 'content', 'image', 'file', 'price', 'private', 'public', 'pinned', 'confirmation_id', 'paid_file', 'date_auction')

class UpdatePostForm(ScheduledPostForm):
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))
    file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))

    class Meta:
        model = Post
        fields = ('feed', 'content', 'image', 'file', 'price', 'private', 'public', 'pinned', 'confirmation_id', 'paid_file', 'date_auction', 'auction_message')

from django.core.validators import MinValueValidator

class UserBidForm(forms.ModelForm):
    bid = forms.IntegerField(required=True)
    user = None
    post = None
    def __init__(self, *args, **kwargs):
        from feed.middleware import get_current_request
        request = get_current_request()
        current = kwargs.pop('current', None)
        super(UserBidForm, self).__init__(*args, **kwargs)
        bid_field = self.fields['bid']
        from translate.translate import translate
        bid_field.validators.append(MinValueValidator(current, message=translate(get_current_request(), 'Please enter a bid higher than the starting bid.')))
        self.fields['bid'].label = translate(get_current_request(), 'Your bid')

    class Meta:
        model = Bid
        fields = ('bid',)

    help_texts = {'bid': 'Please enter a bid higher than the starting bid.'}

class BidForm(forms.ModelForm):
    bid = forms.IntegerField(required=True)
    email = forms.EmailField(required=True)
    post = None
    def __init__(self, *args, **kwargs):
        from feed.middleware import get_current_request
        request = get_current_request()
        current = kwargs.pop('current', None)
        super(BidForm, self).__init__(*args, **kwargs)
        bid_field = self.fields['bid']
        from translate.translate import translate
        bid_field.validators.append(MinValueValidator(current, message=translate(get_current_request(), 'Please enter a bid higher than the starting bid.')))
        self.fields['bid'].label = translate(get_current_request(), 'Your bid')

    class Meta:
        model = Bid
        fields = ('bid',)

    help_texts = {'bid': 'Please enter a bid higher than the starting bid.'}

class ReportForm(forms.ModelForm):
    uid = forms.CharField(max_length=36)
    text = forms.CharField(max_length=1000)

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
#        self.fields['text'].widget.attrs['maxlength'] = max_field_size
    class Meta:
        model = Report
        fields = ('uid', 'text',)
