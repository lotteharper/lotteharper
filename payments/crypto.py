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
    session_key = request.session.session_key
    currency += 'ln' if ln else ''
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

def get_payment_status(payment_id):
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
