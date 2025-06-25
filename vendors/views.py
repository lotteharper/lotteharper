from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import identity_verified, identity_really_verified

def video(request, username):
    from .models import VendorProfile
    from django.shortcuts import redirect
    from django.contrib import messages
    from security.apis import get_client_ip, check_raw_ip_risk
    if not request.COOKIES.get('age_verified', None) or check_raw_ip_risk(get_client_ip(request), True, False):
        messages.warning(request, 'You may not visit this link, as per the site policies.')
        return redirect(reverse('misc:terms'))
    profile = VendorProfile.objects.filter(user__profile__name=username).first()
    return redirect('/' if not profile.video_link else profile.video_link)

def content(request, username):
    from .models import VendorProfile
    from django.shortcuts import redirect
    from django.contrib import messages
    from security.apis import get_client_ip, check_raw_ip_risk
    if not request.COOKIES.get('age_verified', None) or check_raw_ip_risk(get_client_ip(request), True, False):
        messages.warning(request, 'You may not visit this link, as per the site policies.')
        return redirect(reverse('misc:terms'))
    profile = VendorProfile.objects.filter(user__profile__name=username).first()
    return redirect('/' if not profile.content_link else profile.content_link)

@login_required
@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def send_bitcoin(request):
    from .models import VendorPaymentsProfile
    from django.shortcuts import render
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=request.user)
    return render(request, 'vendors/send_bitcoin.html', {'title': 'Crypto', 'info': profile.get_crypto_balances()})

@login_required
@user_passes_test(identity_really_verified, login_url='/verify/', redirect_field_name='next')
def onboarding(request):
    from django.shortcuts import redirect
    from django.urls import reverse
    from payments.models import VendorProfile
    if not hasattr(request.user, 'vendor_profile'):
        v = VendorProfile.objects.create(user=request.user)
        v.save()
        request.user.profile.vendor = True
        request.user.profile.save()
    from django.shortcuts import render
    return redirect(reverse('feed:profile', kwargs={'username': request.user.username}))

@login_required
@user_passes_test(identity_really_verified, login_url='/verify/', redirect_field_name='next')
def vendor_preferences(request):
    from django.shortcuts import redirect
    from django.urls import reverse
    from payments.models import VendorPaymentsProfile
    from .forms import VendorProfileUpdateForm
    from .models import VendorProfile
    from django.contrib import messages
    v, created = VendorProfile.objects.get_or_create(user=request.user)
    v.save()
    form = VendorProfileUpdateForm(instance=v)
    if request.method == 'POST':
        form = VendorProfileUpdateForm(request.POST, request.FILES, instance=request.user.vendor_profile)
        if form.is_valid():
            form.instance.user = request.user
            from payments.apis import validate_address
            accepted = True
            import coinaddrvalidator as crv
            from payments.apis import validate_address
            try:
                if form.cleaned_data.get('payout_address') and not crv.validate(form.cleaned_data.get('payout_currency').lower(), form.cleaned_data.get('payout_address')).valid:
                    form.instance.payout_address = ''
                    messages.warning(request, 'This crypto address could not be accepted. Please check the address and the currency.')
                    accepted = False
            except:
                form.instance.payout_address = ''
                messages.warning(request, 'This crypto address could not be accepted. Please check the address and the currency.')
                accepted = False
            cloc = {'btc': 'bitcoin', 'eth': 'ethereum', 'xlm': 'stellarlumens', 'bch': 'bitcoin-cash', 'ltc': 'litecoin', 'doge': 'dogecoin'}
            cnet = {'usdc': 'usdcoin', 'sol': 'solana', 'matic': 'polygon', 'avax': 'avalanche', 'trump': 'trump', 'usdt': 'usdtether'}
            for key, val in cloc.items():
                try:
                    if form.cleaned_data.get('{}_address'.format(val)) and not crv.validate(key, form.cleaned_data.get('{}_address'.format(val))).valid:
                        exec("form.instance.{}_address = ''".format(val.replace('-', '_')))
                        messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                        accepted = False
                except:
                    exec("form.instance.{}_address = ''".format(val.replace('-', '_')))
                    messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                    accepted = False
            for key, val in cnet.items():
                try:
                    if form.cleaned_data.get('{}_address'.format(val)) and not validate_address(key, form.cleaned_data.get('{}_address'.format(val))):
                        exec("form.instance.{}_address = ''".format(val))
                        messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                        accepted = False
                except:
                    exec("form.instance.{}_address = ''".format(val))
                    messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                    accepted = False
            for char in form.instance.video_intro_color[1:]:
                if char.upper() not in "0123456789ABCDEF":
                    messages.warning(request, 'This color could not be accepted. Please use a hexadecimal color in the form #ABCDEF')
                    form.instance.video_intro_color = '#FFFFFF'
                    accepted = False
            if not form.instance.video_intro_color[0] == '#':
                messages.warning(request, 'This color could not be accepted. Please use a hexadecimal color in the form #ABCDEF')
                form.instance.video_intro_color = '#FFFFFF'
                accepted = False
            from fontTools.ttLib import TTFont
            def validate_ttf(file_path):
                """
                Validates a TTF file.

                Args:
                    file_path (str): The path to the TTF file.

                Returns:
                    bool: True if the TTF file is valid, False otherwise.
                """
                try:
                    font = TTFont(file_path)
                    font.close()
                    return True
                except Exception as e:
                    print(f"Error validating TTF file: {e}")
                    return False
            if form.instance.video_intro_font and not (form.instance.video_intro_font.name.rsplit('.', 1)[1] == 'ttf'):
                messages.warning(request, 'The font you uploaded is not valid because the extension is wrong. Please upload a valid OpenType font in .ttf format.')
                accepted = False
            p = form.save()
            if p.video_intro_font and not (p.video_intro_font.name.rsplit('.', 1)[1] == 'ttf' and validate_ttf(p.video_intro_font.path)):
                messages.warning(request, 'The font you uploaded is not valid. Please upload a valid OpenType font in .ttf format.')
                accepted = False
            if accepted:
                p.user.profile.vendor = True
                p.user.profile.save()
                messages.success(request, 'Vendor profile updated.')
                return redirect(reverse('go:go'))
    from django.conf import settings
    from django.shortcuts import render
    return render(request, 'vendors/vendor_preferences.html', {'title': 'Vendor Preferences','form': form, 'payment_processor': settings.PAYMENT_PROCESSOR, 'vendor': request.user})

