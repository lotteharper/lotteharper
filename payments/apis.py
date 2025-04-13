import requests, json

prices = {}

def get_crypto_price(crypto):
    if crypto == 'USDC': return 1.0
    if crypto == 'ALPH': crypto = 'ETH'
    global prices
    from django.utils import timezone
    if crypto in prices:
        import datetime
        price, time = prices[crypto]
        if time > timezone.now() - datetime.timedelta(minutes=10):
            return price
    currencies = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "BNB": "Binance Coin",
        "ADA": "Cardano",
        "DOGE": "Dogecoin",
        "XRP": "Ripple",
        "LTC": "Litecoin",
        "BCH": "Bitcoin Cash",
        "LINK": "Chainlink",
        "XLM": "Stellar",
        "USDT": "Tether",
        "USDC": "USD Coin",
        "XMR": "Monero",
        "EOS": "EOS",
        "TRX": "TRON",
        "ADA": "Cardano",
        "SOL": "Solana",
        "ATOM": "Cosmos",
        "NEO": "NEO",
        "XEM": "NEM",
        "MIOTA": "IOTA",
        "XTZ": "Tezos",
        "VET": "VeChain",
        "POL": "polygon-ecosystem-token",
        "ETC": "Ethereum Classic",
        "ICP": "Internet Computer",
        "DCR": "Decred"
    }
    from realtime_crypto import RealTimeCrypto
    tracker = RealTimeCrypto()
    try:
        currency = tracker.get_coin(currencies[crypto].lower())
        price = currency.get_price()
        prices[crypto] = (price, timezone.now())
        return price
    except: raise Exception('This currency is not supported at this time.')

def get_crypto_price_nowpayments(crypto):
    if crypto == 'ALPH': crypto = 'ETH'
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
    import json
    print(json.dumps(data))
    try:
        price =  float(data['estimated_amount'])
        prices[crypto] = (price, timezone.now())
        return price
    except: raise Exception('This currency is not supported at this time.')

def validate_address(currency, address):
    from django.conf import settings
    data = {'address': address, 'network': currency.lower()}
    url = "https://api.checkcryptoaddress.com/wallet-checks"
    data = requests.post(url, data=json.dumps(data), headers={'X-Api-Key': settings.CCA_KEY, 'Content-Type': 'application/json'})
#    print(data)
#    print(data.text)
    r = data.json()
    return r['valid'] if 'valid' in r else False

def validate_address_nowpayments(address, currency):
    from django.conf import settings
    data = {'address': address, 'currency': currency}
    url = "https://api.nowpayments.io/v1/payout/validate-address?"
    data = requests.post(url, data=json.dumps(data), headers={'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'})
    return data.text == 'OK'
