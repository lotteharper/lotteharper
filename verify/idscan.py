import requests
import json
from django.conf import settings
import base64
import codecs
from io import BytesIO
from PIL import Image
from verify.forms import get_past_date
from datetime import datetime
from django.utils import timezone
import pytz
utc=pytz.timezone(settings.TIME_ZONE)
#pytz.UTC

def decode_barcode(barcode_data, instance):
    api_url = "https://app1.idware.net/DriverLicenseParserRest.svc/Parse"
    message = barcode_data.encode('utf-8')
    base64_bytes = base64.b64encode(message)
    encoded_string = base64_bytes.decode('utf-8')
    todo = {"authKey": settings.IDSCAN_AUTH_KEY, "text": encoded_string}
    headers =  {"Content-Type":"text/json", "Cache-Control": "no-cache"}
    response = requests.post(api_url, data=json.dumps(todo), headers=headers)
    decoded_data=codecs.decode(response.text.encode(), 'utf-8-sig')
    instance.idscan_text = str(decoded_data)
    instance.idscan = str(decoded_data)
    instance.save()
    print(instance.idscan_text)
    response = json.loads(instance.idscan_text)
    result = response['ParseResult']
    document = result[list(result.keys())[0]]
    if list(result.keys())[0] in settings.BANNED_ID_TYPES: return False
    exp_date = document['ExpirationDate']
    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').replace(tzinfo=utc)
    if exp_date < timezone.now():
        return False
    birthday = document['Birthdate']
    birthday = datetime.strptime(birthday, '%Y-%m-%d').replace(tzinfo=utc)
    subject = document['Subject'] if 'Subject' in document else None
    if settings.REQUIRE_SUBJECTION and subject and not (subject == 'Y' or subject == 'y'): return False
    if birthday > get_past_date().replace(tzinfo=utc):
        return False
    if result['Success'] and int(result['Confidence']) > settings.MIN_CONFIDENCE:
        return True
    return False
