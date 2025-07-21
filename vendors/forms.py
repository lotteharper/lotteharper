from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from .models import VendorProfile
from crypto.currencies import CRYPTO_CURRENCIES
import math


class SendBitcoinForm(forms.Form):
    amount = forms.FloatField()
    bitcoin_address = forms.CharField(min_length=27, max_length=34)

def sub_fee(fee):
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
    for option in get_pricing_options(settings.PRICE_CHOICES):
        choices = choices + [[option, '${} / month'.format(sub_fee(option))]]
    return choices

class VendorProfileUpdateForm(forms.ModelForm):
    PRONOUNS_CHOICES = (
        ('Her', 'She/her/hers'),
        ('Him', 'He/him/his'),
        ('They', 'They/them/theirs'),
        ('Me', 'Just use "me"'),
    )
    pronouns = forms.CharField(widget=forms.Select(choices=PRONOUNS_CHOICES))
    SUBSCRIPTION_CHOICES = (
        ('5', '$5 / month'),
        ('10', '$10 / month'),
        ('15', '$15 / month'),
        ('20', '$20 / month'),
        ('25', '$25 / month'),
        ('50', '$50 / month'),
        ('100', '$100 / month'),
        ('200', '$200 / month'),
        ('500', '$500 / month'),
        ('1000', '$1,000 / month'),
        ('2000', '$2,000 / month'),
    )
    PHOTO_CHOICES = (
        ('5', '$5'),
        ('10', '$10'),
        ('20', '$20'),
        ('25', '$25'),
        ('50', '$50'),
        ('100', '$100'),
    )
    TRIAL_CHOICES = (
        ('0', 'None'),
        ('1', 'One Day'),
        ('2', 'Two Days'),
        ('3', 'Three days'),
        ('7', 'One Week'),
        ('14', 'Two Weeks'),
        ('30', 'One Month'),
        ('60', '60 Days'),
        ('90', '90 Days'),
    )
    CHOICES = list()
    for choice in CRYPTO_CURRENCIES:
        CHOICES.append((choice, choice))
    subscription_fee = forms.CharField(widget=forms.Select(choices=get_pricing()))
    payout_currency = forms.CharField(widget=forms.Select(choices=CHOICES))
    photo_tip = forms.CharField(widget=forms.Select(choices=PHOTO_CHOICES))
    free_trial = forms.CharField(widget=forms.Select(choices=TRIAL_CHOICES))
    payout_address = forms.CharField(max_length=300)
    logo_alpha = forms.FloatField(min_value=0.1, max_value=1)
    pitch_adjust = forms.IntegerField(required=False)
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None')
        super(VendorProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['logo'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['video_intro_font'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        from translate.translate import translate
        from feed.middleware import get_current_request
        r = get_current_request()
        self.fields['logo'].label = translate(r, 'Your square logo', src='en')
        self.fields['video_intro_font'].label = translate(r, 'A font for your video intro', src='en')
        self.fields['video_intro_text'].label = translate(r, 'Text for your video intro', src='en')
        self.fields['video_intro_color'].label = translate(r, 'A color for the intro text', src='en')
        self.fields['hide_profile'].label = translate(r, 'Hide your profile?', src='en')
        self.fields['activate_surrogacy'].label = translate(r, 'Activate contracts for GC/GS? (women only)', src='en')
        self.fields['pronouns'].label = translate(r, 'Please select your pronouns', src='en')
        self.fields['address'].label = translate(r, 'Enter your address', src='en')
        self.fields['insurance_provider'].label = translate(r, 'Your insurance provider', src='en')
        self.fields['video_link'].label = translate(r, 'A link to your video', src='en')
        self.fields['content_link'].label = translate(r, 'A link to your content', src='en')
        self.fields['video_embed'].label = translate(r, 'Your video for embedding', src='en')
        self.fields['playlist_embed'].label = translate(r, 'Your playlist for embedding', src='en')
        self.fields['pitch_adjust'].label = translate(r, 'Your pitch adjustment', src='en')
        self.fields['subscription_fee'].label = translate(r, 'Your subscription fee', src='en')
        self.fields['free_trial'].label = translate(r, 'Free trial options', src='en')
        self.fields['photo_tip'].label = translate(r, 'Default pricing', src='en')
        self.fields['logo_alpha'] = forms.FloatField(
            min_value=0.1,
            max_value=1,
            error_messages={
                'min_value': translate(r, 'Alpha cannot be less than 0.1', src='en'),
                'max_value': translate(r, 'Alpha cannot be greater than 1', src='en')
            })
        self.fields['logo_alpha'].label = translate(r, 'Video intro & logo alpha (0.1-1)', src='en')
        self.fields['payout_currency'].label = translate(r, 'Payout currency', src='en')
        self.fields['payout_address'].label = translate(r, 'Payout address', src='en')
        self.fields['bitcoin_address'].label = translate(r, 'Bitcoin (BTC) address', src='en')
        self.fields['ethereum_address'].label = translate(r, 'Ethereum (ETH) address', src='en')
        self.fields['usdcoin_address'].label = translate(r, 'USDCoin (USDC) address', src='en')
        self.fields['solana_address'].label = translate(r, 'Solana (SOL) address', src='en')
        self.fields['trump_address'].label = translate(r, 'Trump (TRUMP) address', src='en')
        self.fields['polygon_address'].label = translate(r, 'Polygon (POL) address', src='en')
        self.fields['avalanche_address'].label = translate(r, 'Avalanche (AVAX) address', src='en')
        self.fields['bitcoin_cash_address'].label = translate(r, 'Bitcoin Cash (BCH) address', src='en')
        self.fields['litecoin_address'].label = translate(r, 'Litcoin (LTC) address', src='en')
        self.fields['usdtether_address'].label = translate(r, 'USDTether (USDT) address', src='en')
        self.fields['dogecoin_address'].label = translate(r, 'DogeCoin (DOGE) address', src='en')
        if not minor_document_scanned(user): self.fields.pop('activate_surrogacy')

    class Meta:
        model = VendorProfile
        fields = ['logo', 'video_intro_font', 'video_intro_text', 'video_intro_color', 'logo_alpha', 'hide_profile', 'activate_surrogacy', 'pronouns', 'address', 'insurance_provider', 'video_link', 'content_link', 'video_embed', 'playlist_embed', 'pitch_adjust', 'subscription_fee', 'free_trial', 'photo_tip', 'payout_currency', 'payout_address', 'bitcoin_address', 'ethereum_address', 'usdcoin_address', 'solana_address', 'trump_address', 'polygon_address', 'avalanche_address', 'bitcoin_cash_address', 'litecoin_address', 'usdtether_address', 'dogecoin_address']
        labels = {
            'usdcoin_address': 'USDCoin address',
            'usdtether_address': 'USD Tether address',
            'bitcoincash_address': 'Bitcoin Cash address',
            'trump_address': 'TRUMP address',
        }
        widgets = {
            'video_intro_color': forms.TextInput(attrs={'type': 'color'}),
        }
