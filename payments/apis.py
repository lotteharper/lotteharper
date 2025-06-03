import requests, json

prices = {}

def get_trumpcoin_price_ccxt(exchange_id, symbol):
  import ccxt
  """Fetches real-time price data using the CCXT library."""
  exchange = getattr(ccxt, exchange_id)()  # Instantiate the exchange class
  try:
      ticker = exchange.fetch_ticker(symbol)
      return ticker['last'] # Or ticker['bid'], ticker['ask'], etc. based on your needs
  except ccxt.ExchangeError as e:
      return f"Error fetching price from {exchange_id}: {e}"
  except AttributeError as e:
      return f"Invalid exchange: {e}"

def get_trump_price():
  """Fetches the current price of $TRUMP from the CoinGecko API."""

  url = "https://api.coingecko.com/api/v3/simple/price?ids=official-trump&vs_currencies=usd"
  try:
    response = requests.get(url)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    data = response.json()
    trump_price = data['official-trump']['usd']
    return trump_price
  except requests.exceptions.RequestException as e:
      print(f"Error fetching data: {e}")
      return None

if __name__ == "__main__":
  price = get_trump_price()
  if price:
      print(f"The current price of $TRUMP is: ${price}")

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
    if crypto == 'TRUMP':
        return get_trump_price()
    currencies = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binance Coin",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "XRP": "Ripple",
        "LTC": "litecoin",
        "BCH": "bitcoin-cash",
        "LINK": "Chainlink",
        "XLM": "stellar",
        "USDT": "tether",
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
        "DCR": "Decred",
        "TRUMP": "SOL/TRUMP",
        "AVAX": "avalanche",
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

from web3 import Web3

def is_valid_erc20_address(address):
    """
    Checks if the given string is a valid ERC20 address.

    Args:
        address (str): The address string to validate.

    Returns:
        bool: True if the address is valid, False otherwise.
    """
    if not isinstance(address, str):
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
         return Web3.is_address(address)
    except ValueError:
        return False

def validate_address(currency, address):
    from django.conf import settings
    if currency.lower() == 'trump': currency = 'sol'
    if currency.lower() == 'usdt': return is_valid_erc20_address(address)
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
