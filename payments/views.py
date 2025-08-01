from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified, minor_identity_verified, adult_identity_verified
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import patch_cache_control, never_cache
from django.views.decorators.vary import vary_on_cookie

@csrf_exempt
def authorize(request):
    from django.http import HttpResponse
    return HttpResponse(status=200)
    id = request.GET.get('id', None)
    import requests, json
    from .models import Invoice
    invoice = Invoice.objects.get(token=id)
    from payments.crypto import get_payment_status
    from feed.models import Post
    from payments.cart import get_cart_cost
    from django.http import HttpResponse
    if product == 'cart' and float((get_cart_cost(request.COOKIES) if 'cart' in request.COOKIES else 0)) != int(price): return HttpResponse(500)
    if product == 'post' and Post.objects.filter(uuid=pid).first().price != str(price): return HttpResponse(500)
    if product == 'membership' and invoice.model.vendor_profile.subscription_fee != price: return HttpResponse(500)
    if get_payment_status(invoice.number):
        from django.contrib.auth.models import User
        user = invoice.user
        from django.conf import settings
        vendor = invoice.vendor
        from payments.cart import process_cart_purchase
        if invoice.product == 'cart':
            process_cart_purchase(user, invoice.cart)
        if invoice.product == 'invoice':
            from payments.invoice import process_invoice
            process_invoice(invoice)
        if invoice.product == 'post':
            from feed.models import Post
            post = Post.objects.get(author=vendor, id=invoice.pid)
            if not post.paid_file:
                post.recipient = user
                post.save()
                from feed.email import send_photo_email
                send_photo_email(user, post)
            else:
                from feed.email import send_photo_email
                send_photo_email(user, post)
                post.paid_users.add(user)
                post.save()
        if invoice.product == 'surrogacy':
            mother = User.objects.get(profile__stripe_id=account)
            from users.tfa import send_user_text
            send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
            from payments.surrogacy import save_and_send_agreement
            save_and_send_agreement(mother, user)
        if invoice.product == 'webdev':
            from payments.models import PurchasedProduct
            from users.tfa import send_user_text
            PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price), paid=True)
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
        if invoice.product == 'idscan':
            user.profile.idscan_plan = int(price) * 2
            user.profile.idscan_active = True
            user.profile.idscan_used = 0
            user.profile.save()
            user.save()
            from users.tfa import send_user_text
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
        if invoice.product == 'membership':
            user.profile.subscriptions.add(vendor)
            user.profile.save()
            from payments.models import Subscription
            if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True)
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from django.urls import reverse
    r = redirect(reverse('/'))
    if invoice.product == 'cart': clear_cart(r)
    return r


@login_required
@user_passes_test(pediatric_identity_verified)
def send_custom_invoice(request):
    from payments.forms import InvoiceForm
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from django.contrib import messages
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('client_email')
            description = form.cleaned_data.get('description')
            from django.contrib.auth.models import User
            cus_user = User.objects.filter(email=form.cleaned_data.get('client_email', None)).order_by('-profile__last_seen').first()
            print(cus_user)
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('client_email', None)
                print(e)
                if e:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
            from payments.invoice import generate_invoice
            generate_invoice(request.user, cus_user, form.cleaned_data.get('cost'), description)
            messages.success(request, 'This invoice has been sent to {}.'.format(email))
        else: messages.warning(request, 'The form is not valid.')
    return render(request, 'payments/send_invoice.html', {'title': 'Send Invoice', 'form': InvoiceForm(initial={'client_email': request.GET.get('email', None)})})


@never_cache
def pay_invoice(request):
    pid = request.GET.get('pid', None)
    from django.shortcuts import redirect, render
    from django.urls import reverse
    from django.contrib import messages
    if not pid:
        messages.warning(request, 'This invoice could not be found')
        return redirect(reverse('users:login'))
    from payments.models import Invoice
    invoice = Invoice.objects.filter(pid=int(pid)).order_by('-timestamp').first()
    from django.conf import settings
    from .forms import CardPaymentForm
    from django.contrib.auth.models import User
    from contact.forms import ContactForm
    r = render(request, 'payments/pay_invoice.html', {'title': 'Pay Invoice', 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'email_query_delay': 30, 'contact_form': ContactForm(), 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'vendor': invoice.vendor, 'fee': invoice.price, 'invoice': invoice})
    return r

@never_cache
def pay_invoice_crypto(request):
    from django.shortcuts import redirect
    from django.conf import settings
    pid = request.GET.get('pid', None)
    if not pid:
        messages.warning(request, 'This invoice could not be found')
        return redirect(reverse('users:login'))
    if request.method == 'GET' and not request.GET.get('crypto'): return redirect(request.path + '?pid={}&crypto={}'.format(pid, settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto')
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from django.contrib.auth.models import User
    user = User.objects.get(id=settings.MY_ID, profile__vendor=True)
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    from payments.apis import get_crypto_price
    from payments.cart import get_cart_cost
    from payments.cart import get_cart
    from .forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    from payments.apis import get_crypto_price
    from django.shortcuts import redirect, render
    from django.urls import reverse
    from django.contrib import messages
    from payments.models import Invoice
    invoice = Invoice.objects.filter(pid=int(pid)).order_by('-timestamp').first()
    from django.conf import settings
    from .forms import CardPaymentForm
    from django.contrib.auth.models import User
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            from django.contrib import messages
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            print(cus_user)
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                print(e)
                if e:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
#                    except: pass
            from lotteh.celery import validate_cart_payment
            cart_cookie = form.cleaned_data.get('invoice')
            cart_cost = get_cart_cost(cart_cookie, private=True) if 'cart' in request.COOKIES else 0
            fee = format(float(cart_cost) / get_crypto_price(crypto), '.{}f'.format(settings.BITCOIN_DECIMALS))
            fee_reduced = fee.split('.')[0] + '.' + fee.split('.')[1][:settings.BITCOIN_DECIMALS]
            fee = str(float(cart_cost) / get_crypto_price(crypto))
            validate_invoice_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), invoice.id, crypto, network),)
            validate_invoice_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), invoice.id, crypto, network),)
#            validate_cart_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), cart_cookie, crypto, network)
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('payments:subscribe-bitcoin-thankyou', kwargs={'username': user.profile.name}))
        else: print(str(form.errors))
    from payments.cart import get_cart_cost
    from payments.cart import get_cart
    if request.method == 'GET' and request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    from payments.crypto import get_payment_address, get_lightning_address
    cart_cost = invoice.price
    from django.shortcuts import render
    usd_fee = float(cart_cost)
    fee = float(cart_cost) / get_crypto_price(crypto)
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    try:
        address, transaction_id = get_payment_address(user, crypto, fee) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee)
    except:
        address = None
        transaction_id = None
    from feed.models import Post
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    form = BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id, 'invoice': invoice.token}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id, 'invoice': invoice.token})
    from crypto.currencies import CRYPTO_CURRENCIES
    from contact.forms import ContactForm
    r = render(request, 'payments/pay_invoice_crypto.html', {'title': 'Pay Invoice With Crypto', 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'email_query_delay': 30, 'contact_form': ContactForm(), 'helcim_key': settings.HELCIM_KEY, 'vendor': invoice.vendor, 'crypto_address': address, 'currencies': CRYPTO_CURRENCIES, 'username': user.profile.name, 'usd_fee': cart_cost, 'profile': profile, 'form': form, 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'load_timeout': None, 'preload': False, 'stripe_key': settings.STRIPE_PUBLIC_KEY, 'invoice': invoice})
    return r


@csrf_exempt
def crypto_onramp(request, name, address, amount):
    from django.contrib.auth.models import User
    from django.conf import settings
    user = User.objects.get(profile__name=name, profile__vendor=True)
    crypto = request.GET.get('crypto', 'ETH')
    import stripe
    stripe.api_key = settings.STRIPE_API_KEY
    from django.urls import reverse
    import os, json
    currencies = {
        'eth': 'ethereum',
        'btc': 'bitcoin',
        'usdc': 'ethereum',
        'sol': 'solana',
        'matic': 'polygon',
        'pol': 'polygon',
        'xlm': 'stellar',
        'avax': 'avalanche',
        '': '',
    }
    op = os.popen(('curl -X POST https://api.stripe.com/v1/crypto/onramp_sessions -u {} -d "wallet_addresses[' + currencies[crypto.lower()] + ']"="{}" -d "source_currency"="usd" -d "destination_currency"="' + crypto.lower() + '" -d "destination_network"="' + currencies[crypto.lower()] + '" -d "source_amount"="{}" -d "lock_wallet_address"="true"').format(settings.STRIPE_API_KEY, user.vendor_profile.ethereum_address if request.GET.get('tip', False) and False else address, amount)).read()
    print(op)
    out = json.loads(op)
    print(json.dumps(out))
    from django.http import HttpResponse
    return HttpResponse(out['client_secret'])

def clear_cart(response):
    import datetime
    days_expire = 30
    max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie(
        'cart',
        '',
        max_age=max_age,
        expires=expires,
    )

def set_cart(response, cart):
    import datetime
    days_expire = 30
    max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    cart = cart.replace(',', '+')
    response.set_cookie(
        'cart',
        cart,
        max_age=max_age,
        expires=expires,
    )

def combine_cart(cart1, cart2):
    items = {}
    if len(cart1) > 0:
        for item in cart1.replace(' ', ',').replace('+', ',').split(',')[:-1]:
            s = item.split('=')
            if not s: continue
            items[s[0]] = ((items[s[0]] + int(s[1])) if s[0] in items else int(s[1])) if len(s) > 1 else 1
    if len(cart2) > 0:
        for item in cart2.replace(' ', ',').replace('+', ',').split(',')[:-1]:
            s = item.split('=')
            if not s: continue
            items[s[0]] = ((items[s[0]] + int(s[1])) if s[0] in items else int(s[1])) if len(s) > 1 else 1
    cart = ''
    for key, val in items.items():
        if '-' in key and val:
            cart = cart + '{}={},'.format(key, val)
    return cart.rsplit(',', 1)[0] + ','
#    return cart

def cart_card(request):
    from django.conf import settings
    from django.shortcuts import render
    from django.contrib.auth.models import User
    from feed.models import Post
    from .forms import CardPaymentForm
    from django.template.loader import render_to_string
    signature = None
    parent_signature = None
    vendor = User.objects.get(id=settings.MY_ID, profile__vendor=True)
    from payments.cart import get_cart_cost
    from payments.cart import get_cart
    cart_cost = get_cart_cost(request.COOKIES, private=False) if 'cart' in request.COOKIES else 0
    if cart_cost == 0 and not request.GET.get('cart', None):
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        cart_cost = get_cart_cost(request.COOKIES, private=True) if 'cart' in request.COOKIES else 0
        if cart_cost:
            messages.success(request, 'Your cart only contains private items, so you have been redirected to pay with cryptocurrency.')
            return redirect(reverse('payments:cart-crypto'))
        messages.warning(request, 'Your cart is currently empty. Please add a some items to your cart before continuing.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(reverse('/'))
    r = render(request, 'payments/cart_card.html', {'title': 'Shopping Cart', 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'business_type': settings.BUSINESS_TYPE, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'fee': cart_cost if 'cart' in request.COOKIES else 0, 'cart_contents': get_cart(request.COOKIES), 'vendor': vendor, 'default_crypto': settings.DEFAULT_CRYPTO, 'load_timeout': None, 'preload': False, 'payment_processor': 'square', 'cart': request.COOKIES.get('cart', '').replace(',','+'), 'cart_cookie': request.COOKIES.get('cart', '')})
    if request.GET.get('cart', False):
        print(request.GET.get('cart','').replace('+',',').replace(' ', ',').replace('\\', ','))
        print(request.COOKIES.get('cart', ''))
        set_cart(r, combine_cart(request.COOKIES.get('cart', ''), request.GET.get('cart', '').replace('+',',').replace(' ', ',').replace('\\', ',')))
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@never_cache
def cart_crypto(request):
    from django.shortcuts import redirect
    from django.conf import settings
    if request.method == 'GET' and not request.GET.get('crypto'): return redirect(request.path + '?crypto={}'.format(settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto')
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from django.contrib.auth.models import User
    user = User.objects.get(id=settings.MY_ID, profile__vendor=True)
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    from payments.apis import get_crypto_price
    from payments.cart import get_cart_cost
    from payments.cart import get_cart
    from .forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    from payments.apis import get_crypto_price
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            from django.contrib import messages
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            print(cus_user)
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                print(e)
                if e:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
#                    except: pass
            from lotteh.celery import validate_cart_payment
            cart_cookie = form.cleaned_data.get('invoice')
            cart_cost = get_cart_cost(cart_cookie, private=True) if 'cart' in request.COOKIES else 0
            fee = format(float(cart_cost) / get_crypto_price(crypto), '.{}f'.format(settings.BITCOIN_DECIMALS))
            fee_reduced = fee.split('.')[0] + '.' + fee.split('.')[1][:settings.BITCOIN_DECIMALS]
            fee = str(float(cart_cost) / get_crypto_price(crypto))
            validate_cart_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), cart_cookie, crypto, network),)
            validate_cart_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), cart_cookie, crypto, network),)
#            validate_cart_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), cart_cookie, crypto, network)
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('payments:subscribe-bitcoin-thankyou', kwargs={'username': user.profile.name}))
        else: print(str(form.errors))
    from payments.cart import get_cart_cost
    from payments.cart import get_cart
    if request.method == 'GET' and request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    from payments.crypto import get_payment_address, get_lightning_address
    cart_cost = get_cart_cost(request.COOKIES, private=True) if 'cart' in request.COOKIES else 0
    from django.shortcuts import render
    usd_fee = float(cart_cost)
    if usd_fee == 0 and not request.GET.get('cart', None):
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        messages.warning(request, 'Your cart is currently empty. Please add a some items to your cart before continuing.')
        return redirect(reverse('/'))
    fee = float(cart_cost) / get_crypto_price(crypto)
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    try:
        address, transaction_id = get_payment_address(user, crypto, fee) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee)
    except:
        address = None
        transaction_id = None
    from feed.models import Post
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    cart_cookie = request.COOKIES.get('cart') if 'cart' in request.COOKIES else None
    form = BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id, 'invoice': cart_cookie}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id, 'invoice': cart_cookie})
    from crypto.currencies import CRYPTO_CURRENCIES
    if request.user.is_authenticated:
        from lotteh.celery import validate_cart_payment
        cart_cookie = request.COOKIES.get('cart') if 'cart' in request.COOKIES else None
        validate_cart_payment.apply_async(timeout=60*15, args=(request.user.id, user.id, float(fee_reduced) if float(fee_reduced) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced),transaction_id,cart_cookie,crypto,network),)
    r = render(request, 'payments/cart_crypto.html', {'title': 'Checkout with Crypto', 'crypto_address': address, 'currencies': CRYPTO_CURRENCIES, 'username': user.profile.name, 'usd_fee': cart_cost, 'cart_contents': get_cart(request.COOKIES, private=True), 'profile': profile, 'form': form, 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'load_timeout': None, 'preload': False, 'cart': request.COOKIES.get('cart', '').replace(',','+'), 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY})
    if request.GET.get('cart', False):
        set_cart(r, combine_cart(request.COOKIES.get('cart', ''), request.GET.get('cart', '').replace('+',',').replace(' ', ',')))
    return r


@csrf_exempt
def paypal_checkout(request):
    from django.http import HttpResponse
    if not request.method == 'POST': return HttpResponse(200)
    if request.user.is_authenticated: email = request.user.email
    else: email = request.GET.get('email', '')
    from django.contrib.auth.models import User
    product = request.GET.get('product')
    pid = request.GET.get('pid')
    price = request.GET.get('price')
    vendor = request.GET.get('vendor')
    sub = request.GET.get('sub', None)
    model = User.objects.filter(id=str(vendor)).order_by('-profile__last_seen').first()
    import random
    from .models import Invoice
    from django.conf import settings
    from payments.paypal import get_paypal_link
    user = None if User.objects.filter(email=email).count() < 1 else User.objects.filter(email=email).order_by('-profile__last_seen').first()
    if not user:
        from django.utils.crypto import get_random_string
        from users.username_generator import generate_username
        user = User.objects.create_user(email=email, username=generate_username(email), password=get_random_string(8))
        profile = user.profile
        profile.finished_signup = False
        profile.save()
        from users.email import send_verification_email
        from users.password_reset import send_password_reset_email
        send_verification_email(user)
        send_password_reset_email(user)
    else:
        user = None
    product_desc = {
        'webdev': 'Buy a website developed by {}'.format(settings.SITE_NAME),
        'membership': 'Subscribe to {}\'s newsletter membership through {}'.format(model.profile.name, settings.SITE_NAME),
        'idscan': 'Buy an ID scanner plan from {}'.format(settings.SITE_NAME),
        'surrogacy': 'Hire a surrogate mother through {}'.format(settings.SITE_NAME),
        'post': 'An exclusive book, video, photo, and or audio from {} delivered by email.'.format(settings.SITE_NAME),
        'cart': 'Your selected items, photos, books, video and/or audio, delivered electronically.',
        'invoice': 'An invoice from {} for selected goods/services'.format(settings.SITE_NAME)
    }
    from django.utils.crypto import get_random_string
    from payments.cart import get_cart_cost
    from feed.models import Post
    if product == 'cart' and float((get_cart_cost(request.COOKIES) if 'cart' in request.COOKIES else 0)) != int(price): return HttpResponse(500)
    if product == 'post' and Post.objects.filter(uuid=pid).first().price != str(price): return HttpResponse(500)
    if product == 'membership' and model.vendor_profile.subscription_fee != price: return HttpResponse(500)
    token = get_random_string(length=8)
    id, link = get_paypal_link(str(uuid.uuid4()), float(price), token)
    Invoice.objects.create(token=token, user=request.user if request.user.is_authenticated else user, vendor=User.objects.get(id=int(vendor)), number=id, product=product, processor='paypal', price=price, pid=pid, cart=request.COOKIES['cart'] if 'cart' in request.COOKIES else None)
    from django.http import HttpResponse
    import time
    time.sleep(1)
    return HttpResponse(link) #['checkoutToken']


@csrf_exempt
def square_checkout(request):
    from django.http import HttpResponse
    if not request.method == 'POST': return HttpResponse(200)
    if request.user.is_authenticated: email = request.user.email
    else: email = request.GET.get('email', '')
    from django.contrib.auth.models import User
    product = request.GET.get('product')
    pid = request.GET.get('pid')
    price = request.GET.get('price')
    vendor = request.GET.get('vendor')
    sub = request.GET.get('sub', None)
    model = User.objects.filter(id=str(vendor)).order_by('-profile__last_seen').first()
    import random
    from .models import Invoice
    from django.conf import settings
    from payments.square import get_payment_link
    user = None if User.objects.filter(email=email).count() < 1 else User.objects.filter(email=email).order_by('-profile__last_seen').first()
    if not user:
        from django.utils.crypto import get_random_string
        from users.username_generator import generate_username
        user = User.objects.create_user(email=email, username=generate_username(email), password=get_random_string(8))
        profile = user.profile
        profile.finished_signup = False
        profile.save()
        from users.email import send_verification_email
        from users.password_reset import send_password_reset_email
        send_verification_email(user)
        send_password_reset_email(user)
    else:
        user = None
    product_desc = {
        'webdev': 'Buy a website developed by {}'.format(settings.SITE_NAME),
        'membership': 'Subscribe to {}\'s newsletter membership through {}'.format(model.profile.name, settings.SITE_NAME),
        'idscan': 'Buy an ID scanner plan from {}'.format(settings.SITE_NAME),
        'surrogacy': 'Hire a surrogate mother through {}'.format(settings.SITE_NAME),
        'post': 'An exclusive book, video, photo, and or audio from {} delivered by email.'.format(settings.SITE_NAME),
        'cart': 'Your selected items, photos, books, video and/or audio, delivered electronically.',
        'invoice': 'An invoice from {} for selected goods/services'.format(settings.SITE_NAME)
    }
    from django.utils.crypto import get_random_string
    token = get_random_string(length=8)
    from feed.models import Post
    from payments.cart import get_cart_cost
    if product == 'cart' and float((get_cart_cost(request.COOKIES) if 'cart' in request.COOKIES else 0)) != int(price): return HttpResponse(500)
    if product == 'post' and Post.objects.filter(id=int(pid)).first().price != str(price): return HttpResponse(500)
    if product == 'membership' and model.vendor_profile.subscription_fee != price: return HttpResponse(500)
    id, link = get_payment_link(int(price), str(product), 'Customer Order - ' + product.capitalize() + ' - ' + product_desc[product], email, token, subscription=False if not sub else True)
    Invoice.objects.create(token=token, user=request.user if request.user.is_authenticated else user, vendor=User.objects.get(id=int(vendor)), number=id, product=product, price=price, pid=pid, processor='square', cart=request.COOKIES['cart'] if 'cart' in request.COOKIES else '')
    from django.http import HttpResponse
    import time
    time.sleep(1)
    return HttpResponse(link) #['checkoutToken']

def paypal(request):
    import requests, json
    from .models import Invoice
    invoice = Invoice.objects.get(token=request.GET.get('token', None))
    from payments.paypal import get_payment_status
    from feed.models import Post
    from payments.cart import get_cart_cost
    from django.http import HttpResponse
    if product == 'cart' and float((get_cart_cost(request.COOKIES) if 'cart' in request.COOKIES else 0)) != int(price): return HttpResponse(500)
    if product == 'post' and Post.objects.filter(uuid=pid).first().price != str(price): return HttpResponse(500)
    if product == 'membership' and invoice.model.vendor_profile.subscription_fee != price: return HttpResponse(500)
    if get_payment_status(invoice.number):
        from django.contrib.auth.models import User
        user = invoice.user
        from django.conf import settings
        vendor = invoice.vendor
        from payments.cart import process_cart_purchase
        if invoice.product == 'cart':
            process_cart_purchase(user, invoice.cart)
        if invoice.product == 'invoice':
            from payments.invoice import process_invoice
            process_invoice(invoice)
        if invoice.product == 'post':
            from feed.models import Post
            post = Post.objects.get(author=vendor, id=invoice.pid)
            if not post.paid_file:
                post.recipient = user
                post.save()
                from feed.email import send_photo_email
                send_photo_email(user, post)
            else:
                from feed.email import send_photo_email
                send_photo_email(user, post)
                post.paid_users.add(user)
                post.save()
        if invoice.product == 'surrogacy':
            mother = User.objects.get(profile__stripe_id=account)
            from users.tfa import send_user_text
            send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
            from payments.surrogacy import save_and_send_agreement
            save_and_send_agreement(mother, user)
        if invoice.product == 'webdev':
            from payments.models import PurchasedProduct
            from users.tfa import send_user_text
            PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price), paid=True)
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
        if invoice.product == 'idscan':
            user.profile.idscan_plan = int(price) * 2
            user.profile.idscan_active = True
            user.profile.idscan_used = 0
            user.profile.save()
            user.save()
            from users.tfa import send_user_text
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
        if invoice.product == 'membership':
            user.profile.subscriptions.add(vendor)
            user.profile.save()
            from payments.models import Subscription
            if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True)
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from django.urls import reverse
    r = redirect(reverse('/'))
    if invoice.product == 'cart': clear_cart(r)
    return r


def square(request):
    import requests, json
    from django.conf import settings
    from .models import Invoice
    invoice = Invoice.objects.get(token=request.GET.get('token', None))
    headers = {
        'Square-Version': '2024-07-17',
        'Authorization': 'Bearer {}'.format(settings.SQUARE_ACCESS_TOKEN),
        'Content-Type': 'application/json',
    }
    j = requests.post('https://connect.squareup.com/v2/orders/{}'.format(invoice.number), headers=headers).json()
    if j['order']['state'] == 'COMPLETED':
        id = j['order']['id']
        user = invoice.user
        from django.contrib.auth.models import User
        from django.conf import settings
        vendor = invoice.vendor
        if invoice.product == 'cart':
            from payments.cart import process_cart_purchase
            process_cart_purchase(user, invoice.cart)
        if invoice.product == 'invoice':
            from payments.invoice import process_invoice
            process_invoice(invoice)
        if invoice.product == 'post':
            from feed.models import Post
            post = Post.objects.get(author=vendor, id=invoice.pid)
            if not post.paid_file:
                post.recipient = user
                post.save()
                from feed.email import send_photo_email
                send_photo_email(user, post)
            else:
                from feed.email import send_photo_email
                send_photo_email(user, post)
                post.paid_users.add(user)
                post.save()
        if invoice.product == 'surrogacy':
            mother = User.objects.get(profile__stripe_id=account)
            from users.tfa import send_user_text
            send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
            from payments.surrogacy import save_and_send_agreement
            save_and_send_agreement(mother, user)
        if invoice.product == 'webdev':
            from payments.models import PurchasedProduct
            from users.tfa import send_user_text
            PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price), paid=True)
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
        if invoice.product == 'idscan':
            user.profile.idscan_plan = int(price) * 2
            user.profile.idscan_active = True
            user.profile.idscan_used = 0
            user.profile.save()
            user.save()
            from users.tfa import send_user_text
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
        if invoice.product == 'membership':
            user.profile.subscriptions.add(vendor)
            user.profile.save()
            from payments.models import Subscription
            if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True)
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from django.urls import reverse
    r = redirect(reverse('/'))
    if invoice.product == 'cart': clear_cart(r)
    return r

@csrf_exempt
def helcim(request):
    if request.method == 'POST':
        raw = json.loads(request.POST.get('rawDataResponse', None))
        id = raw['invoiceNumber']
        from django.conf import settings
        headers = {
            'api-token': settings.HELCIM_KEY,
            'content-type': 'application/json'
        }
        raw = requests.post('https://api.helcim.com/v2/invoices/' + id, headers=headers).json()
        from .models import Invoice
        invoice = Invoice.objects.get(number=id)
        user = invoice.user
        if raw['status'] == 'PAID':
            from django.contrib.auth.models import User
            from django.conf import settings
            vendor = invoice.vendor
            from payments.cart import process_cart_purchase
            if invoice.product == 'cart':
                process_cart_purchase(user, invoice.cart)
            if invoice.product == 'invoice':
                from payments.invoice import process_invoice
                process_invoice(invoice)
            if invoice.product == 'post':
                from feed.models import Post
                post = Post.objects.get(author=vendor, id=invoice.pid)
                if not post.paid_file:
                    post.recipient = user
                    post.save()
                    from feed.email import send_photo_email
                    send_photo_email(user, post)
                else:
                    from feed.email import send_photo_email
                    send_photo_email(user, post)
                    post.paid_users.add(user)
                    post.save()
            if invoice.product == 'surrogacy':
                mother = User.objects.get(profile__stripe_id=account)
                from users.tfa import send_user_text
                send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
                from payments.surrogacy import save_and_send_agreement
                save_and_send_agreement(mother, user)
            if invoice.product == 'webdev':
                from payments.models import PurchasedProduct
                from users.tfa import send_user_text
                PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price), paid=True)
                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
            if invoice.product == 'idscan':
                user.profile.idscan_plan = int(price) * 2
                user.profile.idscan_active = True
                user.profile.idscan_used = 0
                user.profile.save()
                user.save()
                from users.tfa import send_user_text
                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
            if invoice.product == 'membership':
                user.profile.subscriptions.add(vendor)
                user.profile.save()
                from payments.models import Subscription
                if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True)
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from django.urls import reverse
    r = redirect(reverse('/'))
    if invoice.product == 'cart': clear_cart(r)
    return r

@csrf_exempt
def invoice(request):
    from django.http import HttpResponse
    if not request.method == 'POST': return HttpResponse(200)
    if request.user.is_authenticated: email = request.user.email
    else: email = request.GET.get('email', '')
    product = request.GET.get('product')
    pid = request.GET.get('pid')
    price = request.GET.get('price')
    vendor = request.GET.get('vendor')
    import random
    from .models import Invoice
    from django.conf import settings
    from feed.models import Post
    from payments.cart import get_cart_cost
    if product == 'cart' and float((get_cart_cost(request.COOKIES) if 'cart' in request.COOKIES else 0)) != float(price): return HttpResponse(500)
    if product == 'post' and Post.objects.filter(uuid=pid).first().price != str(price): return HttpResponse(500)
    if product == 'membership' and model.vendor_profile.subscription_fee != price: return HttpResponse(500)
    headers = {
        'api-token': settings.HELCIM_KEY,
        'content-type': 'application/json'
    }
    payload1 = {
        'currency': 'USD',
        'lineItems': [{'sku': pid, 'description': product, 'quantity': 1, 'price': int(price)}]
    }
    import requests, json
    resp1 = requests.post('https://api.helcim.com/v2/invoices/', data=json.dumps(payload1), headers=headers).json()
    inv = resp1['invoiceNumber']
    payload = {
        'paymentType': 'purchase', 'amount': int(price), 'currency': 'USD', 'invoiceNumber': inv,
    }
    resp = requests.post('https://api.helcim.com/v2/helcim-pay/initialize', data=json.dumps(payload), headers=headers).json()
    print(resp)
    from django.contrib.auth.models import User
    user = None if User.objects.filter(email=email).count() < 1 else User.objects.filter(email=email).order_by('-profile__last_seen').first()
    if not user:
        from django.utils.crypto import get_random_string
        from users.username_generator import generate_username
        user = User.objects.create_user(email=email, username=generate_username(email), password=get_random_string(8))
        profile = user.profile
        profile.finished_signup = False
        profile.save()
        security_profile = SecurityProfile.objects.create(user=user)
        security_profile.save()
        from users.email import send_verification_email
        from users.password_reset import send_password_reset_email
        send_verification_email(user)
        send_password_reset_email(user)
    else:
        user = None
    Invoice.objects.create(user=request.user if request.user.is_authenticated else user, vendor=User.objects.get(id=int(vendor)), number=inv, product=product, price=price, pid=pid, processor='helcim',)
    from django.http import HttpResponse
    return HttpResponse(json.dumps(resp)) #['checkoutToken']

def render_agreement(name, parent, mother, lang=None):
    from django.conf import settings
    if lang == None: lang = settings.DEFAULT_LANG
    from django.utils import timezone
    from django.template.loader import render_to_string
    from feed.templatetags.nts import nts
    class GetParams():
        lang = None
        def __init__(self, lang, *args, **kwargs):
            self.lang = lang

        def get(self, param, other=False):
            return self.lang

    class DummyUser():
        is_authenticated = False

    class DummyRequest():
        GET = None
        LANGUAGE_CODE = None
        user = None
        def __init__(self, lang, *args, **kwargs):
            self.GET = GetParams(lang)
            self.LANGUAGE_CODE = lang
            self.user = DummyUser()
    request = DummyRequest(lang)
    return render_to_string('payments/surrogacy.txt', {
        'request': request,
        'the_clinic_name': settings.FERTILITY_CLINIC,
        'the_site_name': settings.SITE_NAME,
        'mother_name': name,
        'mother_address': mother.vendor_profile.address,
        'mother_insurance': mother.vendor_profile.insurance_provider,
        'the_state_name': 'Washington',
        'parent_name': parent.verifications.last().full_name if parent and parent.verifications.last() else '________________',
        'surrogacy_fee': nts(settings.SURROGACY_FEE),
        'surrogacy_fee_sub': settings.SURROGACY_FEE,
        'business_type': settings.BUSINESS_TYPE,
        'the_date': timezone.now().strftime('%B %d, %Y'),
    })

@vary_on_cookie
@cache_page(60*60*24*365)
def cancel(request):
    from django.shortcuts import render
    from contact.forms import ContactForm
    r = render(request, 'payments/cancel_payment.html', {'title':'We\'re sad to see you go', 'contact_form': ContactForm(), 'preload': False})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@vary_on_cookie
@cache_page(60*60*24*365)
def success(request):
    from django.shortcuts import render
    r = render(request, 'payments/success.html', {'title': 'Thank you for your payment', 'preload': False})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    if request.GET.get('cart', False): clear_cart(r)
    return r

@vary_on_cookie
@cache_page(60*60*24*365)
def webdev(request):
    from django.shortcuts import render
    from django.conf import settings
    from payments.stripe import WEBDEV_DESCRIPTIONS
    prices = ['100', '200', '500', '1000', '2000', '5000']
    price_dev = []
    for x in range(0, len(prices)):
        price_dev = price_dev + [{'price': prices[x], 'description': WEBDEV_DESCRIPTIONS[x]}]
    from contact.forms import ContactForm
    from .forms import CardPaymentForm
    from django.contrib.auth.models import User
    r = render(request, 'payments/webdev.html', {'title': 'Web Development Pricing', 'plans': price_dev, 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'email_query_delay': 30, 'contact_form': ContactForm(), 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'vendor': User.objects.get(id=settings.MY_ID)})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@vary_on_cookie
@cache_page(60*60*24*365)
def idscan(request):
    from django.conf import settings
    from django.shortcuts import render
    price_scans = ['5','10', '20', '50', '100', '200', '500', '1000', '2000', '5000']
    from .forms import CardPaymentForm
    from django.contrib.auth.models import User
    r = render(request, 'payments/idscan.html', {'title': 'ID Scanner Pricing', 'plans': price_scans, 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'email_query_delay': 30, 'free_trial': settings.IDSCAN_TRIAL_DAYS, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'vendor': User.objects.get(id=settings.MY_ID)})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@cache_page(60*60*24*365)
@vary_on_cookie
#@never_cache
def surrogacy(request, username):
    from django.conf import settings
    from django.shortcuts import render
    from django.contrib.auth.models import User
    from feed.models import Post
    from django.template.loader import render_to_string
    from .forms import CardPaymentForm
    signature = None
    parent_signature = None
    vendor = User.objects.filter(profile__name=username, profile__vendor=True, vendor_profile__activate_surrogacy=True).order_by('-profile__last_seen').first()
    if not vendor:
        from django.shortcuts import redirect
        from django.urls import reverse
        from django.contrib import messages
        messages.warning(request, '@{} is not accepting surrogacy contracts at the moment. Please stay in touch and revisit in the future.'.format(username))
        if request.user.is_authenticated: return redirect(reverse('app:app'))
        else: return redirect(reverse('users:login'))
    if vendor.verifications.filter(verified=True).last(): signature = render_to_string('raw_signature.html', {'theuser': vendor})
    if request.user.is_authenticated and request.user.verifications.last(): parent_signature = render_to_string('raw_signature.html', {'theuser': request.user})
    from translate.translate import translate
    inp_t = translate(request, 'Intended Parent')
    sgm_t = translate(request, 'Surrogate Mother')
    agreement = render_agreement(vendor.profile.name if not vendor.verifications.last() else vendor.verifications.last().full_name, request.user if request.user.is_authenticated else None, vendor).replace('__________________________________, Surrogate Mother', '{}, {}'.format(signature if signature else '__________________________________', sgm_t), 1).replace('__________________________________, Intended Parent', '{}, {}'.format(parent_signature if parent_signature else '__________________________________', inp_t), 1)
    post_ids = Post.objects.filter(public=True, private=False, published=True, feed='private').exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    r = render(request, 'payments/surrogacy.html', {'title': 'Surrogacy Plans', 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'post': post, 'vendor': vendor, 'agreement': agreement, 'surrogacy_fee': settings.SURROGACY_FEE, 'business_type': settings.BUSINESS_TYPE, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'preload': False, 'down_payment': settings.SURROGACY_DOWN_PAYMENT, 'weekly_payment': (settings.SURROGACY_FEE - settings.SURROGACY_DOWN_PAYMENT)/36})
#    return r
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@vary_on_cookie
@cache_page(60*60*24*7)
def surrogacy_info(request, username):
    from django.conf import settings
    from django.shortcuts import render
    from django.contrib.auth.models import User
    from feed.models import Post
    from contact.forms import ContactForm
    vendor = User.objects.get(profile__name=username, profile__vendor=True)
    post_ids = Post.objects.filter(public=True, private=False, published=True, feed='private').exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    r = render(request, 'payments/surrogacy_info.html', {'title': 'Surrogacy Plan Information', 'post': post, 'vendor': vendor, 'surrogacy_fee': settings.SURROGACY_FEE, 'contact_form': ContactForm(), 'preload': False})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r


@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def connect_account(request):
    from django.shortcuts import redirect
    from .stripe import create_connected_account
    return redirect(create_connected_account(request.user.id))

@login_required
def model_subscription_cancel(request, username):
    import stripe
    from django.contrib.auth.models import User
    from payments.models import Subscription
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.urls import reverse
    vendor = User.objects.get(profile__name=username, profile__vendor=True)
    for sub in Subscription.objects.filter(user=request.user, model=vendor, active=True):
        stripe.Subscription.delete(sub.stripe_subscription_id)
        sub.active = False
        sub.save()
        messages.success(request, 'You have cancelled your subscription. Please consider another plan.')
    return redirect(reverse('app:app'))

@login_required
def subscription_cancel(request):
    import stripe
    from django.urls import reverse
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.user.profile.idscan_active:
        stripe.Subscription.delete(request.user.profile.stripe_subscription_id)
        request.user.profile.idscan_active = False
        request.user.profile.save()
        request.user.save()
        messages.success(request, 'You have cancelled your subscription. Please consider another plan.')
    return redirect(reverse('payments:idscan'))

@login_required
def webdev_subscription_cancel(request):
    import stripe
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.urls import reverse
    if request.user.profile.webdev_active:
        stripe.Subscription.delete(request.user.profile.stripe_subscription_service_id)
        request.user.profile.webdev_active = False
        request.user.profile.save()
        request.user.save()
        messages.success(request, 'You have cancelled your subscription. Please consider another plan.')
    return redirect(reverse('payments:webdev'))

@csrf_exempt
def webhook(request):
    payload = request.body
    event = None
    import stripe
    from django.conf import settings
    stripe.api_key = settings.STRIPE_API_KEY
    from payments.stripe import PRICE_IDS
    from payments.stripe import PROFILE_MEMBERSHIP_PRICE_IDS
    from payments.stripe import PHOTO_PRICE_IDS
    from payments.stripe import WEBDEV_PRICE_IDS
    from payments.stripe import WEBDEV_MONTHLY_PRICE_IDS
    from payments.stripe import WEBDEV_DESCRIPTIONS
    from payments.stripe import PROFILE_MEMBERSHIP
    from payments.stripe import PHOTO_PRICE
    from payments.stripe import CART_ID
    from payments.models import Subscription, PurchasedProduct
    from users.models import Profile
    from security.models import SecurityProfile
    price_scans = ['5','10', '20', '50', '100', '200', '500', '1000', '2000', '5000']
    price_dev = ['100', '200', '500', '1000', '2000', '5000']
    try:
        import json
        event = stripe.Event.construct_from(
            json.loads(payload), settings.STRIPE_API_KEY
        )
    except ValueError as e:
        from django.http import HttpResponse
        return HttpResponse(status=400)
    session = event.data['object']
    account = None
    invoice = stripe.Invoice.retrieve(session.get('invoice'))
    account = invoice['transfer_data']['destination'] if invoice['transfer_data'] else None
    print(str(invoice))
    if event.type == 'checkout.session.completed' or event.type == 'charge.captured' or event.type == 'charge.succeeded' or event.type == 'customer.subscripton.resumed' or event.type == 'invoice.created' or event.type == 'invoice.paid':
#        print(str(session))
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get("subscription")
        stripe_price_id = None
        stripe_product_id = None
        line_items = stripe.checkout.Session.list_line_items(session.get('id'))['data'][0]
        try: stripe_price_id = line_items['price']['id']
        except: pass
        try: stripe_product_id = line_items['price']['product']
        except: pass
        print('price: {}, prod: {}'.format(stripe_price_id, stripe_product_id))
#        account = session.get("account")
        metadata = session.get("metadata")
        email = session.get('customer_details')['email'] if 'email' in session.get('customer_details').keys() else session.get('customer_email')
        print(email)
        from django.contrib.auth.models import User
        user = None if User.objects.filter(email=email).count() < 1 else User.objects.filter(email=email).order_by('-profile__last_seen').first()
        if not user:
            from django.utils.crypto import get_random_string
            from users.username_generator import generate_username
            user = User.objects.create_user(email=email, username=generate_username(email), password=get_random_string(8))
            profile = user.profile
            profile.finished_signup = False
            profile.save()
            client_reference_id = user.id
            user.profile.stripe_customer_id = stripe_customer_id
            if stripe_price_id in WEBDEV_MONTHLY_PRICE_IDS:
                user.profile.stripe_subscription_service_id = stripe_subscription_id
            else:
                user.profile.stripe_subscription_id = stripe_subscription_id
            user.profile.save()
            from users.email import send_verification_email
            from users.password_reset import send_password_reset_email
            send_verification_email(user)
            send_password_reset_email(user)
        else:
            user = None
            try: user = User.objects.get(id = client_reference_id)
            except: user = User.objects.filter(email=email).order_by('-profile__last_seen').first()
            user.profile.stripe_customer_id = stripe_customer_id,
            if stripe_price_id in WEBDEV_MONTHLY_PRICE_IDS:
                user.profile.stripe_subscription_service_id = stripe_subscription_id
            else:
                user.profile.stripe_subscription_id = stripe_subscription_id
            user.profile.save()
        print(user.username)
        print('Checking for idscan plan')
        try:
            plan = PRICE_IDS.index(stripe_price_id)
            user.profile.idscan_plan = int(price_scans[plan]) * 2
            user.profile.idscan_active = True
            user.profile.idscan_used = 0
            user.profile.save()
            user.save()
            from users.tfa import send_user_text
            send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
        except:
            print('None found, checking for webdev')
            try:
                product = WEBDEV_PRICE_IDS.index(stripe_price_id)
                product_desc = WEBDEV_DESCRIPTIONS[product]
                from payments.models import PurchasedProduct
                from users.tfa import send_user_text
                PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price_dev[product]), paid=True)
                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
            except:
                print('Checking for profile membership')
                if account and stripe_product_id == PROFILE_MEMBERSHIP:
                    vendor = User.objects.get(profile__stripe_id=account)
                    user.profile.subscriptions.add(vendor)
                    user.profile.save()
                    from payments.models import Subscription
                    if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True, strip_subscription_id=stripe_subscription_id)
                elif account and stripe_product_id == PHOTO_PRICE:
                    vendor = User.objects.get(profile__stripe_id=account)
                    from feed.models import Post
                    post = Post.objects.get(author=vendor, id=int(metadata[0]))
                    if not post.paid_file:
                        post.recipient = user
                        post.save()
                        from feed.email import send_photo_email
                        send_photo_email(user, post)
                    else:
                        from feed.email import send_photo_email
                        send_photo_email(user, post)
                        post.paid_users.add(user)
                        post.save()
                elif account and stripe_product_id == CART_ID:
                    from payments.cart import process_cart_purchase
                    invoice = Invoice.objects.filter(pid=int(metadata[0])).first()
                    if invoice and invoice.product == 'cart':
                        process_cart_purchase(user, invoice.cart)
                else:
                    from .stripe import SURROGACY_PRICE_ID
                    if SURROGACY_PRICE_ID == stripe_price_id:
                        mother = User.objects.get(profile__stripe_id=account)
                        from users.tfa import send_user_text
                        send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
                        from payments.surrogacy import save_and_send_agreement
                        save_and_send_agreement(mother, user)
                    else:
                        try:
                            product = WEBDEV_MONTHLY_PRICE_IDS.index(stripe_price_id)
                            if product != None:
                                user.profile.webdev_plan = int(price_dev[product])
                                user.profile.webdev_active = True
                                user.profile.save()
                                from payments.models import PurchasedProduct
                                PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price_dev[product]), paid=True, monthly=True)
                                from users.tfa import send_user_text
                                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
                        except: pass
    elif event.type == 'charge.failed' or event.type == 'charge.refunded' or event.type == 'customer.subscripton.deleted' or event.type == 'customer.subscripton.paused' or event.type == 'invoice.deleted':
        session = event.data['object']
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get("subscription")
        stripe_price_id = None
        stripe_product_id = None
        line_items = stripe.checkout.Session.list_line_items(session.get('id'))['data'][0]
        try: stripe_price_id = line_items['price']['id']
        except: pass
        try: stripe_product_id = line_items['price']['product']
        except: pass
        print('price: {}, prod: {}'.format(stripe_price_id, stripe_product_id))
        from django.contrib.auth.models import User
        try:
            plan = PRICE_IDS.index(stripe_price_id)
            user = User.objects.get(profile__stripe_customer_id=stripe_customer_id)
            user.profile.idscan_active = False
            user.profile.save()
            user.save()
        except:
            if stripe_product_id == PROFILE_MEMBERSHIP and account:
                vendor = User.objects.get(profile__stripe_id=account)
                user.profile.subscriptions.remove(vendor)
                user.profile.save()
    else:
        print('Unhandled event type {}'.format(event.type))
    from django.http import HttpResponse
    return HttpResponse(status=200)

@csrf_exempt
def monthly_checkout_profile(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    import random
    plan = int(request.GET.get('plan'))
    price_scans = [5, 10, 15, 20, 25, 50, 75, 100, 200, 500, 1000, 2000, 5000]
    id = price_scans.index(plan)
    from payments.stripe import PROFILE_MEMBERSHIP_PRICE_IDS
    from payments.stripe import PROFILE_MEMBERSHIP
    price = PROFILE_MEMBERSHIP_PRICE_IDS[0] # id
    vendor = User.objects.get(profile__stripe_id=request.GET.get('vendor', None))
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        cus_user = User.objects.filter(email=request.GET.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
            from email_validator import validate_email
            e = form.cleaned_data.get('email', None)
            if e:
                try:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
                except: pass
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                customer_email = request.GET.get('email', None),
                success_url=domain_url + "/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancel/",
                payment_method_types= ["card", "us_bank_account"],
                mode = "subscription",
                line_items=[
                    {
                        "price_data": {"currency": settings.CURRENCY, "unit_amount": int(plan * 100), "product": PROFILE_MEMBERSHIP, "recurring": {"interval": "month"}},
                        "quantity": 1
                    }
                ],
                allow_promotion_codes=True,
                subscription_data={
                    "trial_period_days": int(vendor.vendor_profile.free_trial) if int(vendor.vendor_profile.free_trial) > 0 else None,
                    "application_fee_percent": settings.APPLICATION_FEE,
                    "transfer_data": {"destination": request.GET.get('vendor', None)},
                } if request.GET.get('vendor', None) else None,
            )
            print(checkout_session)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@csrf_exempt
def monthly_checkout(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    import random
    plan = int(request.GET.get('plan'))
    price_scans = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    id = price_scans.index(plan)
    from payments.stripe import PRICE_IDS
    price = PRICE_IDS[id]
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        cus_user = User.objects.filter(email=request.GET.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
            from email_validator import validate_email
            e = form.cleaned_data.get('email', None)
            if e:
                try:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
                except: pass
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                customer_email = request.GET.get('email', None),
                success_url=domain_url + "/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancel/",
                payment_method_types= ["card", "us_bank_account"],
                mode = "subscription",
                line_items=[
                    {
                        "price": price,
                        "quantity": 1
                    }
                ],
                allow_promotion_codes=True,
                subscription_data={
                    "trial_period_days": settings.IDSCAN_TRIAL_DAYS if id < 3 else 0,
                    "application_fee_percent": settings.APPLICATION_FEE,
                    "transfer_data": {"destination": request.GET.get('vendor', None)},
                } if False and request.GET.get('vendor', None) else None,
            )
            print(checkout_session)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@csrf_exempt
def onetime_checkout_photo(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    from feed.models import Post
    import random
    photo = request.GET.get('photo', None)
    vendor = Post.objects.filter(id=int(photo)).first().author
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        cus_user = User.objects.filter(email=request.GET.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
            from email_validator import validate_email
            e = form.cleaned_data.get('email', None)
            if e:
                try:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
                except: pass
        try:
            from payments.stripe import PHOTO_PRICE
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                success_url=domain_url + "/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancel/",
                customer_email = request.GET.get('email', None),
                payment_method_types= ["card", "us_bank_account"],
                mode = "payment",
                line_items=[
                    {
                        "price_data": {"currency": settings.CURRENCY, "unit_amount": int(float(Post.objects.filter(id=str(photo)).first().price) * 100), "product": PHOTO_PRICE},
                        "quantity": 1
                    }
                ],
                metadata = [photo],
                allow_promotion_codes=True,
                payment_intent_data={
                    "application_fee_amount": settings.APPLICATION_FEE_PHOTO,
                    "transfer_data": {"destination": vendor.profile.stripe_id},
                },
            )
            print(checkout_session)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@csrf_exempt
def onetime_checkout_cart(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    from feed.models import Post
    import random
    from payments.cart import get_cart_cost
    cart_cookie = dict(request.headers.items())['Cart']
    total = get_cart_cost(cart_cookie, private=False) if 'Cart' in request.headers.keys() else 0
    vendor = User.objects.get(id=settings.MY_ID)
    pid = random.randint(111111, 999999)
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        cus_user = User.objects.filter(email=request.GET.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
            from email_validator import validate_email
            e = form.cleaned_data.get('email', None)
            if e:
                try:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
                except: pass
        try:
            from payments.stripe import CART_ID
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                success_url=domain_url + "/payments/success/?{}".format('cart=t&'),
                cancel_url=domain_url + "/payments/cancel/",
                payment_method_types= ["card", "us_bank_account"],
                customer_email = request.GET.get('email', None),
                mode = "payment",
                line_items=[
                    {
                        "price_data": {"currency": settings.CURRENCY, "unit_amount": int(float(total) * 100), "product": CART_ID},
                        "quantity": 1
                    }
                ],
                metadata = [pid],
                allow_promotion_codes=True,
                payment_intent_data={
                    "application_fee_amount": settings.APPLICATION_FEE_PHOTO,
                    "transfer_data": {"destination": vendor.profile.stripe_id},
                },
            )
            from django.utils.crypto import get_random_string
            token = get_random_string(length=8)
            from payments.models import Invoice
            number = ''
            Invoice.objects.create(token=token, user=request.user if request.user.is_authenticated else cus_user, vendor=User.objects.get(id=int(vendor.id)), number=id, product='cart', processor='stripe', price=total, pid=pid, cart=request.COOKIES['cart'] if 'cart' in request.COOKIES else None)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@csrf_exempt
def onetime_checkout(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    import random
    plan = int(request.GET.get('plan'))
    monthly = request.GET.get('monthly', False) != False
    price_scans = [100, 200, 500, 1000, 2000, 5000]
    id = price_scans.index(plan)
    from payments.stripe import WEBDEV_PRICE_IDS, WEBDEV_MONTHLY_PRICE_IDS
    price = WEBDEV_PRICE_IDS[id] if not monthly else WEBDEV_MONTHLY_PRICE_IDS[id]
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        cus_user = User.objects.filter(email=request.GET.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
            from email_validator import validate_email
            e = form.cleaned_data.get('email', None)
            if e:
                try:
                    from security.apis import check_raw_ip_risk
                    from security.models import SecurityProfile
                    from users.models import Profile
                    from users.email import send_verification_email, sendwelcomeemail
                    from users.views import send_registration_push
                    valid = validate_email(e, check_deliverability=True)
                    us = User.objects.filter(email=e).last()
                    safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                    if valid and not us and safe:
                        cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                        profile = cus_user.profile
                        profile.finished_signup = False
                        profile.save()
                        messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                        send_verification_email(cus_user)
                        send_registration_push(cus_user)
                        sendwelcomeemail(cus_user)
                except: pass
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                customer_email = request.GET.get('email', None),
                success_url=domain_url + "/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancel/",
                payment_method_types= ["card", "us_bank_account"],
                mode = "payment" if not monthly else "subscription",
                line_items=[
                    {
                        "price": price,
                        "quantity": 1
                    }
                ],
                allow_promotion_codes=True,
                payment_intent_data={
                    "application_fee_percent": settings.APPLICATION_FEE,
                    "transfer_data": {"destination": request.GET.get('vendor', None)},
                } if request.GET.get('vendor', None) else None,
            )
            print(checkout_session)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@csrf_exempt
def onetime_checkout_surrogacy(request):
    import stripe
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import JsonResponse
    from payments.stripe import SURROGACY_PRICE_ID
    import random
    vendor = User.objects.get(id=int(request.GET.get('vendor', None)), vendor_profile__activate_surrogacy=True)
    price = SURROGACY_PRICE_ID
    if request.method == "GET":
        domain_url = settings.BASE_URL
        stripe.api_key = settings.STRIPE_API_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else random.randint(111111,999999),
                customer_email = request.GET.get('email', None),
                success_url=domain_url + "/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancel/",
                payment_method_types= ["card", "us_bank_account"],
                mode = "payment",
                line_items=[
                    {
                        "price": price,
                        "quantity": 1
                    }
                ],
                allow_promotion_codes=True,
                payment_intent_data={
                    "application_fee_amount": settings.APPLICATION_FEE_SURROGACY,
                    "transfer_data": {"destination": vendor.profile.stripe_id},
                } if request.GET.get('vendor', None) else None,
            )
            print(checkout_session)
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)})

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def card_list(request):
    from .models import PaymentCard
    from django.shortcuts import render
    cards = PaymentCard.objects.filter(user=request.user).order_by('-primary')
    return render(request, 'payments/payment_cards.html', {'title': 'Payment Cards', 'cards': cards, 'preload': False})

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def card_primary(request, id):
    from django.http import HttpResponse
    from payments.models import PaymentCard
    card = PaymentCard.objects.filter(id=int(id)).first()
    if request.method == 'POST':
        from django.contrib import messages
        for c in PaymentCard.objects.filter(user=request.user):
            c.primary = False
            c.save()
        card.primary = True
        card.save()
        messages.success(request, 'The card ending in *{} is now your primary payment card.'.format(str(card.number)[12:]))
    return HttpResponse('<i class="bi bi-pin-angle-fill"></i>' if card.primary else '<i class="bi bi-pin-fill"></i>')

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def card_delete(request, id):
    from django.http import HttpResponse
    from payments.models import PaymentCard
    if request.method == 'POST':
        from django.contrib import messages
        card = PaymentCard.objects.filter(id=int(id)).first()
        messages.success(request, 'The card ending in *{} was deleted.'.format(str(card.number if card and card.number else '****************')[12:]))
        if card: card.delete()
    return HttpResponse('Deleted')


@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def cancel_subscription(request, username):
    from django.contrib.auth.models import User
    from django.shortcuts import redirect
    from django.urls import reverse
    import stripe
    model = User.objects.get(profile__name=username, profile__vendor=True)
    if not model in request.user.profile.subscriptions.all():
        return redirect(reverse('feed:profile', kwargs={'username': model.profile.name}))
    fee = model.vendor_profile.subscription_fee
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_API_KEY
        stripe.Subscription.delete(sub.stripe_subscription_id)
        from payments.models import Subscription
        sub = Subscription.objects.filter(active=True, model=model, user=request.user).last()
        sub.active = False
        sub.save()
        request.user.profile.subscriptions.delete(remove)
        request.user.profile.save()
        from django.contrib import Messages
        messages.success(request, 'You have cancelled your subscription.')
        return redirect(reverse('feed:home'))
    from django.shortcuts import render
    return render(request, 'payments/cancel.html', {
        'title': 'Cancel Subscription',
        'model': model,
        'preload': False
    })

@vary_on_cookie
@cache_page(60*60*24*7)
def subscribe_card(request, username):
    from django.contrib.auth.models import User
    from feed.models import Post
    from django.shortcuts import redirect
    from django.urls import reverse
    from .forms import CardPaymentForm
    user = User.objects.get(profile__name=username, profile__vendor=True)
    if hasattr(request, 'user') and request.user.is_authenticated and user in request.user.profile.subscriptions.all():
        return redirect(reverse('feed:profile', kwargs={'username': user.profile.name}))
    profile = user.profile
    fee = user.vendor_profile.subscription_fee
    from django.conf import settings
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    from django.shortcuts import render
    r = render(request, 'payments/subscribe_card.html', {'title': 'Subscribe', 'username': username, 'profile': profile, 'fee': fee, 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'model': user.profile, 'post': post, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'payment_processor': 'stripe'})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r


@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def tip_card(request, username, tip):
    from django.contrib.auth.models import User
    from .forms import CardNumberForm, CardInfoForm
    from .models import PaymentCard, CardPayment
    from django.contrib import messages
    from .forms import CardPaymentForm
    fee = tip
    user = User.objects.get(profile__name=username, profile__vendor=True)
    profile = user.profile
    if request.method == 'POST':
        num_form = CardNumberForm(request.user,request.POST)
        card = None
        if num_form.is_valid():
            if PaymentCard.objects.filter(user=request.user, number=num_form.cleaned_data.get('number')).count() > 0: card = PaymentCard.objects.filter(user=request.user, number=num_form.cleaned_data.get('number')).last()
            else: card = num_form.save()
        else:
            messages.warning(request, num_form.errors)
        info_form = CardInfoForm(request.user, request.POST, instance=card)
        if info_form.is_valid():
            if info_form.cleaned_data.get('expiry_year') < 2000:
                info_form.instance.expiry_year = info_form.cleaned_data.get('expiry_year') - 2000
            card = info_form.save()
        else:
            messages.warning(request, info_form.errors)
            card.delete()
            card = None
        if card:
#            from payments.authorizenet import pay_fee
#            if pay_fee(user, fee, card, name='Tip to {}\'s profile'.format(user.profile.name), description='One time tip for adult webcam modeling content.'):
            if False:
                CardPayment.objects.create(user=request.user, amount=fee)
                from users.tfa import send_user_text
                send_user_text(user, '{} has tipped you ${}, {}.'.format(request.user.profile.name, fee, user.profile.preferred_name))
                messages.success(request, 'Your payment was processed. Thank you for the tip!')
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('feed:profile', kwargs={'username': user.profile.name}))
            else:
                messages.warning(request, 'Your payment wasn\'t processed successfully. Please try a new form of payment.')
    from django.shortcuts import render
    r = render(request, 'payments/tip_card.html', {'title': 'Tip With Credit or Debit Card', 'username': username, 'profile': profile, 'card_info_form': CardInfoForm(request.user), 'card_number_form': CardNumberForm(request.user, initial={'address': request.user.verifications.last().address if request.user.verifications.last() else ''}), 'fee': fee, 'username': username, 'profile': profile, 'usd_fee': fee, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'load_timeout': None})
    return r


@never_cache
def subscribe_bitcoin_thankyou(request, username):
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    if request.user.is_authenticated and user in request.user.profile.subscriptions.all():
        from django.contrib import messages
        messages.success(request, 'Your payment has been verified. Thank you for subscribing! - {}'.format(user.profile.name))
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('feed:profile', kwargs={'username': user.profile.name}))
    from django.shortcuts import render
    from django.conf import settings
    return render(request, 'payments/subscribe_bitcoin_thankyou.html', {'title': 'Thanks - {}'.format(settings.SITE_NAME), 'profile': user.profile})

#@login_required
#@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
def subscribe_bitcoin(request, username):
    from django.shortcuts import redirect
    from django.conf import settings
    if not request.GET.get('crypto'): return redirect(request.path + '?crypto={}'.format(settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto') if request.GET.get('crypto') else 'BTC'
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from django.contrib import messages
    from django.urls import reverse
    if request.user.is_authenticated and user in request.user.profile.subscriptions.all():
        return redirect(reverse('feed:profile', kwargs={'username': user.profile.name}))
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    usd_fee = user.vendor_profile.subscription_fee
    from .forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                if e:
                    try:
                        from security.apis import check_raw_ip_risk
                        from security.models import SecurityProfile
                        from users.models import Profile
                        from users.email import send_verification_email, sendwelcomeemail
                        from users.views import send_registration_push
                        valid = validate_email(e, check_deliverability=True)
                        us = User.objects.filter(email=e).last()
                        safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                        if valid and not us and safe:
                            cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                            profile = cus_user.profile
                            profile.finished_signup = False
                            profile.save()
                            messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                            send_verification_email(cus_user)
                            send_registration_push(cus_user)
                            sendwelcomeemail(cus_user)
                    except: pass
            from lotteh.celery import validate_bitcoin_payment
            validate_bitcoin_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network),)
            validate_bitcoin_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network),)
            validate_bitcoin_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network)
            return redirect(reverse('payments:subscribe-bitcoin-thankyou', kwargs={'username': user.profile.name}))
    from payments.apis import get_crypto_price
    fee = float(user.vendor_profile.subscription_fee) / get_crypto_price(crypto)
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    try:
        address, transaction_id = get_payment_address(user, crypto, fee) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee)
    except:
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        messages.warning(request, 'This transaction could not be completed because the payment is less than minimal for the currency requested. Please select a new payment currency, or pay in lightning.')
        return redirect(request.path + '?lightning=t&crypto=BTC')
    from lotteh.celery import validate_bitcoin_payment
    if request.user.is_authenticated: validate_bitcoin_payment.apply_async(timeout=60*10, args=(request.user.id, user.id, float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE, transaction_id, usd_fee,crypto,network),)
    from feed.models import Post
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    from django.shortcuts import render
    from crypto.currencies import CRYPTO_CURRENCIES
    return render(request, 'payments/subscribe_crypto.html', {'title': 'Subscribe with Crypto', 'model': user.profile, 'username': username, 'vendor_profile': profile, 'profile': profile, 'form': BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}), 'crypto_address': address, 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'currencies': CRYPTO_CURRENCIES, 'post': post, 'model': user.profile, 'load_timeout': None, 'preload': False, 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY})

#@login_required
#@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
@never_cache
def tip_bitcoin_thankyou(request, username):
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from django.shortcuts import render
    return render(request, 'payments/tip_bitcoin_thankyou.html', {'title': 'Thanks - {}', 'profile': user.profile, 'preload': False})

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def tip_bitcoin(request, username, tip):
    from django.conf import settings
    from django.shortcuts import redirect
    if not request.GET.get('crypto'): return redirect(request.path + '?crypto={}'.format(settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto')
    from django.contrib.auth.modles import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from .models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    from .forms import BitcoinPaymentForm
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST)
        if form.is_valid():
            return redirect(reverse('payments:tip-bitcoin-thankyou', kwargs={'username': user.profile.name}))
    from .apis import get_crypto_price
    fee = format(round(float(tip) / get_crypto_price(crypto), settings.BITCOIN_DECIMALS), '.{}f'.format(settings.BITCOIN_DECIMALS))
    fee_reduced = fee.split('.')[0] + '.' + fee.split('.')[1][:settings.BITCOIN_DECIMALS]
    usd_fee = tip
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    address, transaction_id = get_payment_address(user, crypto, fee_reduced) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee_reduced)
    from feed.models import Post
    from crypto.currencies import CRYPTO_CURRENCIES
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    from django.shortcuts import render
    return render(request, 'payments/tip_crypto.html', {'title': 'Tip with Crypto', 'username': username, 'crypto_address': address, 'profile': profile, 'form': BitcoinPaymentForm(initial={'amount': str(fee_reduced)}), 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'currencies': CRYPTO_CURRENCIES, 'post': post, 'load_timeout': None, 'preload': False, 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY})

#@vary_on_cookie
#@cache_page(60*60*3)
def buy_photo_crypto(request, username):
    from security.middleware import get_qs
    from django.conf import settings
    from django.shortcuts import redirect
    from security.middleware import get_qs
    if not request.GET.get('crypto'): return redirect(request.path + '?' + get_qs(request.GET) + '&crypto={}'.format(settings.DEFAULT_CRYPTO) + ('&lightning=t' if request.GET.get('lightning', None) else ''))
    crypto = request.GET.get('crypto')
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    from django.utils import timezone
    import datetime
    from feed.models import Post
    uid = None
    if not request.GET.get('id'):
        if request.COOKIES.get('age_verified', False):
            uid = Post.objects.filter(author=user, public=False, published=True, recipient=None, date_auction__lte=timezone.now() - datetime.timedelta(days=365)).exclude(image=None).order_by('?').first().uuid
        else:
            uid = Post.objects.filter(author=user, private=False, published=True, recipient=None, date_auction__lte=timezone.now() - datetime.timedelta(days=365)).exclude(image=None).order_by('?').first().uuid
        return redirect(request.path + '?crypto={}&id={}'.format(crypto, uid) + ('&lightning=t' if request.GET.get('lightning', None) else ''))
    id = request.GET.get('id', None)
    post = Post.objects.filter(uuid=id, date_auction__lte=timezone.now()).first()
    if not post:
        if request.COOKIES.get('age_verified', False):
            post = Post.objects.filter(author=user, public=False, published=True, recipient=None, date_auction__lte=timezone.now() - datetime.timedelta(days=365)).exclude(image=None).order_by('?').first()
        else:
            post = Post.objects.filter(author=user, private=False, published=True, recipient=None, date_auction__lte=timezone.now() - datetime.timedelta(days=365)).exclude(image=None).order_by('?').first()
    tip = int(post.price)
    from .apis import get_crypto_price
    fee = round(float(tip) / get_crypto_price(crypto), settings.BITCOIN_DECIMALS)
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    usd_fee = tip
    from payments.forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                if e:
                    try:
                        from security.apis import check_raw_ip_risk
                        from security.models import SecurityProfile
                        from users.models import Profile
                        from users.email import send_verification_email, sendwelcomeemail
                        from users.views import send_registration_push
                        valid = validate_email(e, check_deliverability=True)
                        us = User.objects.filter(email=e).last()
                        safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                        if valid and not us and safe:
                            cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                            profile = cus_user.profile
                            profile.finished_signup = False
                            profile.save()
                            messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                            send_verification_email(cus_user)
                            send_registration_push(cus_user)
                            sendwelcomeemail(cus_user)
                    except: pass
            from django.contrib import messages
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            from lotteh.celery import validate_photo_payment
            validate_photo_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network),)
            validate_photo_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network),)
            validate_photo_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), usd_fee,crypto,network)
            from django.urls import reverse
            return redirect(post.get_absolute_url())
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    try:
        address, transaction_id = get_payment_address(user, crypto, fee_reduced) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee_reduced)
    except:
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        messages.warning(request, 'This transaction could not be completed because the payment is less than minimal for the currency requested. Please select a new payment currency, or pay in lightning.')
        return redirect(request.path + '?lightning=t&id={}&crypto=BTC'.format(post.id))
    from django.shortcuts import render
    from crypto.currencies import CRYPTO_CURRENCIES
    if request.user.is_authenticated:
        from lotteh.celery import validate_photo_payment
        validate_photo_payment.apply_async(timeout=60*5, args=(request.user.id, user.id, float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE, transaction_id, id, crypto, network),)
    r = render(request, 'payments/buy_photo_crypto.html', {'title': 'Buy this item with Crypto', 'username': username, 'crypto_address': address, 'profile': profile, 'form': BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}), 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'currencies': CRYPTO_CURRENCIES, 'post': post, 'load_timeout': None, 'preload': False, 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY})
#    if request.user.is_authenticated: patch_cache_control(r, private=True)
#    else: patch_cache_control(r, public=True)
    return r

@vary_on_cookie
@cache_page(60*60*24*7)
def buy_photo_card(request, username):
    from security.middleware import get_qs
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    fee = user.vendor_profile.photo_tip
    from django.shortcuts import redirect
    from feed.models import Post
    from django.utils import timezone
    import datetime
    if not request.GET.get('id'): return redirect(request.path + '?id={}{}'.format(Post.objects.filter(author=user, private=False, published=True, recipient=None, date_auction__lte=timezone.now() - datetime.timedelta(days=365)).exclude(image=None).order_by('?').first().uuid, get_qs(request.GET) if (len(request.GET.keys()) > 0) else ''))
    id = request.GET.get('id', None)
    post = Post.objects.filter(uuid=id, date_auction__lte=timezone.now(), private=False).first()
    from django.shortcuts import render
    from django.conf import settings
    from .forms import CardPaymentForm
    r = render(request, 'payments/buy_photo_card.html', {'title': 'Buy this item with Credit or Debit Card', 'username': username, 'profile': profile, 'fee': post.price, 'post': post, 'stripe_pubkey': settings.STRIPE_PUBLIC_KEY, 'helcim_key': settings.HELCIM_KEY, 'form': CardPaymentForm(), 'load_timeout': None, 'payment_processor': 'square'})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def charge_card(request):
    user = request.user
    from .forms import CardNumberForm, PaymentForm
    from .models import VendorPaymentsProfile, PaymentCard, CardPayment
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    if request.method == 'POST':
        from django.contrib import messages
        num_form = CardNumberForm(request.user,request.POST)
        card = None
        if num_form.is_valid():
            if PaymentCard.objects.filter(user=request.user, number=num_form.cleaned_data.get('number')).count() > 0: card = PaymentCard.objects.filter(user=request.user, number=num_form.cleaned_data.get('number')).last()
            else: card = num_form.save()
        else:
            messages.warning(request, num_form.errors)
        info_form = CardInfoForm(request.user, request.POST, instance=card)
        if info_form.is_valid():
            if form.cleaned_data.get('expiry_month') != 'MM' and form.cleaned_data.get('expiry_year') != 'YY':
                card = info_form.save()
            else:
                messages.warning(request, 'Please choose an expiration date in the form.')
                card.delete()
                card = None
        else:
            messages.warning(request, info_form.errors)
            card.delete()
        if card:
            payment_form = PaymentForm(request.POST)
#            from payments.authorizenet import pay_fee
            if not payment_form.is_valid(): messages.warning(request, 'The form could not be validated.')
#            elif pay_fee(user, payment_form.cleaned_data.get('total'), card, customer_type=payment_form.cleaned_data.get('customer_type'), full_name=payment_form.cleaned_data.get('full_name'), name=payment_form.cleaned_data.get('item_name'), description=payment_form.cleaned_data.get('description')):
            if False:
                messages.success(request, 'The payment was processed.')
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('go:go'))
            else:
                messages.warning(request, 'Your payment wasn\'t processed successfully. Please try a new form of payment.')
    from django.shortcuts import render
    return render(request, 'payments/charge_card.html', {'title': 'Charge a Credit or Debit Card', 'card_info_form': CardInfoForm(request.user), 'card_number_form': CardNumberForm(request.user), 'payment_form': PaymentForm(), 'username': profile.vendor.profile.name, 'helcim_key': settings.HELCIM_KEY, 'load_timeout': None, 'preload': False})

#@vary_on_cookie
#@cache_page(60*60*3)
@never_cache
def tip_crypto_simple(request, username):
    from django.shortcuts import redirect
    from django.conf import settings
    if not request.GET.get('crypto'): return redirect(request.path + '?crypto={}'.format(settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto')
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True)
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    from payments.crypto import get_payment_address
    from payments.apis import get_crypto_price
    fee = float(100 if not request.GET.get('tip', None) else request.GET.get('tip')) / get_crypto_price(crypto)
    fee_reduced = format(float(fee), '.{}f'.format(settings.BITCOIN_DECIMALS)) #fee.split('.')[0] + '.' + fee.split('.')[1][:settings.BITCOIN_DECIMALS]
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from feed.models import Post
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    from .forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    from django.contrib import messages
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            if (not cus_user) or not (cus_user and cus_user.email != '' and cus_user.email != None):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                if e:
                    try:
                        from security.apis import check_raw_ip_risk
                        from security.models import SecurityProfile
                        from users.models import Profile
                        from users.email import send_verification_email, sendwelcomeemail
                        from users.views import send_registration_push
                        valid = validate_email(e, check_deliverability=True)
                        us = User.objects.filter(email=e).last()
                        safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                        if valid and not us and safe:
                            cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                            profile = cus_user.profile
                            profile.finished_signup = False
                            profile.save()
                            messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                            send_verification_email(cus_user)
                            send_registration_push(cus_user)
                            sendwelcomeemail(cus_user)
                    except: pass
            from lotteh.celery import validate_tip_payment
            validate_tip_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'),crypto,network),)
            validate_tip_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'),crypto,network),)
            validate_tip_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), crypto, network)
            from django.urls import reverse
            return redirect(reverse('payments:subscribe-bitcoin-thankyou', kwargs={'username': user.profile.name}))
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    address, transaction_id = get_payment_address(user, crypto, fee_reduced, tip=True) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee_reduced, ln=True, tip=True)
    from lotteh.celery import validate_tip_payment
    if request.user.is_authenticated: validate_tip_payment.apply_async(timeout=60*10, args=(request.user.id, user.id, float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE, transaction_id,crypto,network),)
    from django.shortcuts import render
    from crypto.currencies import CRYPTO_CURRENCIES
    r = render(request, 'payments/tip_crypto_simple.html', {'title': 'Send a Tip in Crypto', 'usd_fee': request.GET.get('tip', 100) , 'crypto_fee': fee_reduced, 'address': address, 'currencies': CRYPTO_CURRENCIES, 'username': user.profile.name, 'post': post, 'load_timeout': None, 'form': BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}), 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY})
#    if request.user.is_authenticated: patch_cache_control(r, private=True)
#    else: patch_cache_control(r, public=True)
    return r

@login_required
@user_passes_test(adult_identity_verified, login_url='/verify/', redirect_field_name='next')
def surrogacy_crypto(request, username):
    from django.shortcuts import redirect
    from django.conf import settings
    if not request.GET.get('crypto'): return redirect(request.path + '?crypto={}'.format(settings.DEFAULT_CRYPTO))
    crypto = request.GET.get('crypto') if request.GET.get('crypto') else 'BTC'
    network = None if not request.GET.get('lightning', False) else 'lightning'
    from django.contrib.auth.models import User
    user = User.objects.get(profile__name=username, profile__vendor=True, vendor_profile__activate_surrogacy=True)
    from django.contrib import messages
    from django.urls import reverse
    from payments.models import VendorPaymentsProfile
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=user)
    usd_fee = settings.SURROGACY_DOWN_PAYMENT
    from .forms import BitcoinPaymentForm, BitcoinPaymentFormUser
    from payments.apis import get_crypto_price
    fee = round(float(settings.SURROGACY_DOWN_PAYMENT) / get_crypto_price(crypto), settings.BITCOIN_DECIMALS)
    fee_reduced = format(fee, '.{}f'.format(settings.BITCOIN_DECIMALS))
    if request.method == 'POST':
        form = BitcoinPaymentForm(request.POST) if not request.user.is_authenticated else BitcoinPaymentFormUser(request.POST)
        if form.is_valid():
            messages.success(request, 'We are validating your crypto payment. Please allow up to 15 minutes for this process to take place.')
            cus_user = User.objects.filter(email=form.cleaned_data.get('email', None)).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
            if (not cus_user):
                from email_validator import validate_email
                e = form.cleaned_data.get('email', None)
                if e:
                    try:
                        from security.apis import check_raw_ip_risk
                        from security.models import SecurityProfile
                        from users.models import Profile
                        from users.email import send_verification_email, sendwelcomeemail
                        from users.views import send_registration_push
                        valid = validate_email(e, check_deliverability=True)
                        us = User.objects.filter(email=e).last()
                        safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
                        if valid and not us and safe:
                            cus_user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                            profile = cus_user.profile
                            profile.finished_signup = False
                            profile.save()
                            messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                            send_verification_email(cus_user)
                            send_registration_push(cus_user)
                            sendwelcomeemail(cus_user)
                    except: pass
            from lotteh.celery import validate_surrogacy_payment
            validate_surrogacy_payment.apply_async(timeout=60*5, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), crypto, network),)
            validate_surrogacy_payment.apply_async(timeout=60*10, args=(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), crypto, network),)
            validate_surrogacy_payment(cus_user.id, user.id, float(form.data['amount']) if float(form.data['amount']) > float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE else float(fee_reduced), form.cleaned_data.get('transaction_id'), crypto, network)
            return redirect(reverse('payments:subscribe-bitcoin-thankyou', kwargs={'username': user.profile.name}))
    from payments.crypto import get_payment_address, get_lightning_address
    if request.GET.get('lightning', None) and crypto != 'BTC': return redirect(request.path + '?lightning=t&crypto=BTC')
    address, transaction_id = get_payment_address(user, crypto, fee) if not request.GET.get('lightning') else get_lightning_address(user, crypto, fee)
    from lotteh.celery import validate_surrogacy_payment
    validate_surrogacy_payment.apply_async(timeout=60*10, args=(request.user.id, user.id, float(fee_reduced) * settings.MIN_BITCOIN_PERCENTAGE, transaction_id, crypto, network),)
    from feed.models import Post
    post_ids = Post.objects.filter(public=True, private=False, published=True).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=post_ids).order_by('?').first()
    from django.shortcuts import render
    from crypto.currencies import CRYPTO_CURRENCIES
    return render(request, 'payments/surrogacy_crypto.html', {'title': 'Pay with Crypto', 'model': user.profile, 'surrogacy_fee': settings.SURROGACY_FEE, 'username': username, 'vendor_profile': profile, 'profile': profile, 'form': BitcoinPaymentForm(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}) if not request.user.is_authenticated else BitcoinPaymentFormUser(initial={'amount': str(fee_reduced), 'transaction_id': transaction_id}), 'crypto_address': address, 'crypto_fee': fee_reduced, 'usd_fee': usd_fee, 'currencies': CRYPTO_CURRENCIES, 'post': post, 'model': user.profile, 'load_timeout': None, 'preload': False, 'bitcoin_address': user.vendor_profile.bitcoin_address, 'ethereum_address': user.vendor_profile.ethereum_address, 'stripe_key': settings.STRIPE_PUBLIC_KEY, 'down_payment': settings.SURROGACY_DOWN_PAYMENT, 'weekly_payment': (settings.SURROGACY_FEE - settings.SURROGACY_DOWN_PAYMENT)/36})

