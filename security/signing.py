def check_signature(token):
    import requests, json
    key = requests.get('https://auth.vivokey.com/.well-known/jwks.json').json()['keys'][0]['pem']
    print(key)
    import jwt
    try:
        decoded_token = jwt.decode(token, key, algorithms=['ES256'])
        return decoded_token
    except:
        import traceback
        print(traceback.format_exc())
    return False
