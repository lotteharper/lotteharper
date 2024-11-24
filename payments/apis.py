import requests, json

prices = {}

def get_crypto_price(crypto):
    global prices
    from django.utils import timezone
    if crypto in prices:
        import datetime
        price, time = prices[crypto]
        if time > timezone.now() - datetime.timedelta(minutes=10):
            return price
    from django.conf import settings
    url = "https://api.nowpayments.io/v1/estimate?amount=1.0&currency_from={}&currency_to=usd".format(crypto)
    data = requests.get(url, headers={'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'})
    data = data.json()
    try:
        price =  float(data['estimated_amount'])
        prices[crypto] = (price, timezone.now())
    except: raise Exception('This currency is not supported at this time.')

def validate_address(address, currency):
    from django.conf import settings
    data = {'address': address, 'currency': currency}
    url = "https://api.nowpayments.io/v1/payout/validate-address?"
    data = requests.post(url, data=json.dumps(data), headers={'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'})
    return data.text == 'OK'
