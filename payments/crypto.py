import requests
import json
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from feed.middleware import get_current_request
from django.contrib import messages

def get_bearer_token():
    data = {
        "email": settings.NOWPAYMENTS_EMAIL,
        "password": settings.NOWPAYMENTS_PASSWORD,
    }
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/auth', headers=headers, data=json.dumps(data))
    data = output.json()
    return data['token']

def generate_sub_partner(id):
    data = {
        "name": str(id) + '-BD',
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/balance', data=json.dumps(data), headers=headers)
    data = output.json()
    return data['result']['id']


addresses = {}

def get_lightning_address(model, currency, amount, ln=True, tip=False):
    global addresses
    from django.utils import timezone
    request = get_current_request()
    currency += 'ln' if ln else ''
    if request:
        session_key = request.session.session_key
        if tip and (currency in addresses and (session_key in addresses[currency]) and (amount in addresses[currency][session_key])):
            import datetime
            address, payment_id, time = addresses[currency][session_key][amount]
            if time > timezone.now() - datetime.timedelta(minutes=10):
                return address, payment_id
    data = {'currency': 'BTC', 'amount': str(round(float(amount) * 100000000))}
    headers = {"Authorization": "{}".format(settings.OPENNODE_KEY), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.opennode.com/v1/charges', data=json.dumps(data), headers=headers)
    data = output.json()
    print(output)
    print(output.text)
    if tip:
        if not currency in addresses:
            addresses[currency] = {}
        if not session_key in addresses[currency]:
            addresses[currency][session_key] = {}
        addresses[currency][session_key][amount] = (data['data']['lightning_invoice']['payreq'], data['data']['id'], timezone.now()) if ln else (data['data']['address'], data['data']['order_id'], timezone.now())
    return (data['data']['lightning_invoice']['payreq'], data['data']['id']) if ln else (data['data']['address'], data['data']['order_id'])

def get_payment_address(model, currency, amount, tip=False):
    if currency == 'BTC': return get_lightning_address(model, currency, amount, ln=False, tip=tip)
    if currency == 'ALPH': currency = 'ETH'
    global addresses
    from django.utils import timezone
    request = get_current_request()
    if request:
        session_key = request.session.session_key
        if tip and (currency in addresses and (session_key in addresses[currency])):
            import datetime
            address, payment_id, time = addresses[currency][session_key]
            if time > timezone.now() - datetime.timedelta(minutes=30):
                return address, payment_id
    from cryptapi import CryptAPIHelper
    import random
    from django.urls import reverse
    from django.conf import settings
    order_id = random.randrange(11111111, 99999999)
    payable_addresses = {
        'BTC': model.vendor_profile.bitcoin_address,
        'ETH': model.vendor_profile.ethereum_address,
        'USDC': model.vendor_profile.usdcoin_address,
        'SOL': model.vendor_profile.solana_address,
        'POL': model.vendor_profile.polygon_address,
        'XLM': model.vendor_profile.stellarlumens_address,
        'TRUMP': model.vendor_profile.trump_address,
        'BCH': model.vendor_profile.bitcoin_cash_address,
        'LTC': model.vendor_profile.litecoin_address,
        'USDT': model.vendor_profile.usdtether_address,
        'DOGE': model.vendor_profile.dogecoin_address,
        'AVAX': model.vendor_profile.avalanche_address,
    }
    tickers = {
        'BTC': 'btc',
        'ETH': 'eth',
        'POL': 'polygon/pol',
        'AVAX': 'avax-c/avax',
        'SOL': 'sol/sol',
        'USDC': 'base/usdc',
        'USDT': 'erc20/usdt',
        'LTC': 'ltc',
        'DOGE': 'doge',
        'TRUMP': 'sol/trump',
        'BCH': 'bch',
#        'USDP': 'erc20/usdp'
    }
    try:
        ca = CryptAPIHelper(tickers[currency], payable_addresses[currency], settings.BASE_URL + reverse('payments:authorize'), {'orderid': order_id}, {'post': 1})
        pay_address = ca.get_address()['address_in']
        if tip:
            if not currency in addresses:
                addresses[currency] = {}
            addresses[currency][session_key] = pay_address, order_id, timezone.now()
        return pay_address, order_id
    except:
        from .exceptions import PaymentLessThanMinimalException
        raise PaymentLessThanMinimalException('This crypto payment received an error or was less than minimal and cannot be completed. Try using another payment method, or another product.')

def get_payment_address_nowpayments(model, currency, amount, tip=False):
    if currency == 'BTC': return get_lightning_address(model, currency, amount, ln=False, tip=tip)
    if currency == 'ALPH': currency = 'ETH'
    global addresses
    from django.utils import timezone
    request = get_current_request()
    session_key = request.session.session_key
    if tip and (currency in addresses and (session_key in addresses[currency])):
        import datetime
        address, payment_id, time = addresses[currency][session_key]
        if time > timezone.now() - datetime.timedelta(minutes=30):
            return address, payment_id
#    id = str(model.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "price_amount": str(amount),
        "price_currency": currency.lower(),
        "pay_currency": currency.lower(),
        "payout_address": model.vendor_profile.payout_address,
        "payout_currency": model.vendor_profile.payout_currency
#        "sub_partner_id": id,
#        "fixed_rate": False
    }
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/payment', data=json.dumps(data), headers=headers)
    data = output.json()
    print(data)
    try:
        if tip:
            if not currency in addresses:
                addresses[currency] = {}
            addresses[currency][session_key] = data['pay_address'], data['payment_id'], timezone.now()
        return data['pay_address'], data['payment_id']
    except:
        from .exceptions import PaymentLessThanMinimalException
        raise PaymentLessThanMinimalException('This crypto payment is less than minimal and cannot be completed. Try using another payment method, or another product.')

def get_payment_address_sub_partner(model, currency, amount):
    id = str(model.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "currency": currency.lower(),
        "amount": str(amount),
        "sub_partner_id": id,
        "fixed_rate": False
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/payment', data=json.dumps(data), headers=headers)
    data = output.json()
#    print(data)
    return data['result']['pay_address'], data['result']['payment_id']

def get_lightning_status(payment_id):
    headers = {"Authorization": "{}".format(settings.OPENNODE_KEY), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.get('https://api.opennode.com/v2/charge/{}'.format(payment_id), headers=headers)
    data = output.json()
#    print(output.text)
    return float(data['data']['fee'])/1000000.0 if data['data']['status'] == 'paid' else 0

def get_payment_status(payment_id, crypto, address):
    from cryptapi import CryptAPIHelper
    from django.conf import settings
    from django.urls import reverse
    url = settings.BASE_URL + reverse('payments:authorize') + '?orderid={}&orderid={}'.format(payment_id, payment_id)
    ca = CryptAPIHelper(crypto.lower(), address, url, {'orderid': payment_id}, {'post': 1})
    data = ca.get_logs()
    print(data)
    paid = 0
    if 'callbacks' in data and len(data['callbacks']) > 0 and 'value_coin' in data['callbacks'][0]:
        for callback in data['callbacks']: paid = paid + callback['value_coin']
    return paid

def get_payment_status_nowpayments(payment_id):
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY}
    output = requests.get('https://api.nowpayments.io/v1/payment/{}'.format(payment_id), headers=headers)
    data = output.json()
    return float(data['actually_paid'])

def get_sub_partner_balance(id):
    id = str(id)
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY}
    output = requests.get('https://api.nowpayments.io/v1/sub-partner/balance/{}'.format(id), headers=headers)
    print(output)
    data = output.json()
    return data['result']['balances']

def sweep_all_to_master():
    for user in User.objects.filter(profile__vendor=True):
        id = str(user.vendor_payments_profile.first().get_sub_partner_id())
        for coin, balance in get_sub_partner_balance(id):
            sweep_to_master(user, coin, balance['amount'])

def sweep_to_master(user, currency, amount):
    id = str(user.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "currency": currency,
        "amount": amount,
        "sub_partner_id": id
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/write-off', data=json.dumps(data), headers=headers)
    data = output.json()
    return data
