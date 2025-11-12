import traceback
import requests
import json
from .models import UserIpAddress
from requests.auth import HTTPBasicAuth
from django.conf import settings
import ipaddress

HACKERGUARDIAN_RANGES = [] # ['64.39.96.0/20', '139.87.112.0/23']

FRAUDGUARD_USER = settings.FRAUDGUARD_USER
FRAUDGUARD_SECRET = settings.FRAUDGUARD_SECRET
ANTIDEO_KEY = settings.ANTIDEO_KEY

RISK_LEVEL = 1

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def ip_in_range(ip_addr):
    for range in HACKERGUARDIAN_RANGES:
        if ipaddress.ip_address(ip_addr) in ipaddress.ip_network(range): return True
    return False

import ipaddress

def get_ip_version(ip_string):
    """
    Checks if an IP address string is IPv4 or IPv6.

    Args:
        ip_string: The IP address string to check.

    Returns:
        "IPv4" if the address is IPv4, "IPv6" if it's IPv6,
        or None if the string is not a valid IP address.
    """
    try:
        ip_obj = ipaddress.ip_address(ip_string)
        if ip_obj.version == 4:
            return "IPv4"
        elif ip_obj.version == 6:
            return "IPv6"
    except ValueError:
        return None

def check_ip_risk(ip_addr, soft=False, dummy=False):
    if dummy: return False
    if ip_in_range(ip_addr.ip_address): return False
    from IPQualityScore.DBReader import DBReader
    try:
        record = DBReader(str(settings.BASE_DIR) + f"/security/IPQualityScore-IP-Reputation-Database-{get_ip_version(ip_addr.ip_address)}.ipqs").Fetch(ip_addr.ip_address)
        if record.IsBlacklisted():
            ip_addr.risk_detected = True
            ip_addr.risk_recheck = False
            ip_addr.save()
            return not soft
        if record.IsTOR():
            ip_addr.risk_detected = True
            ip_addr.risk_recheck = False
            ip_addr.save()
            return not soft
        if record.IsBot():
            ip_addr.risk_detected = True
            ip_addr.risk_recheck = False
            ip_addr.save()
            return not soft
        if record.RecentAbuse():
            ip_addr.risk_detected = True
            ip_addr.risk_recheck = False
            ip_addr.save()
            return not soft
    except: pass
    try:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_addr.ip_address}"
        headers = {"accept": "application/json", "x-apikey": settings.VIRUSTOTAL_API_KEY}
        response = requests.get(url, headers=headers)
        result = response.json()
        stats = result['data']['attributes']['last_analysis_stats']
        if stats['malicious'] > 0 or stats['suspicious'] > 0:
            ip_addr.risk_detected = True
            ip_addr.risk_recheck = False
            ip_addr.save()
            return not soft
        else:
            ip_addr.risk_detected = False
            ip_addr.risk_recheck = False
            ip_addr.save()
            return False
        try:
            headers = {
                'Key': settings.ABUSEIPDB_KEY,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip_addr.ip_address,
                'maxAgeInDays': 90,
                'verbose': True
            }
            response = requests.get('https://api.abuseipdb.com/api/v2/check', headers=headers, params=params)
            result = response.json()
            if result['data']['abuseConfidenceScore'] > 0:
                ip_addr.risk_detected = True
                ip_addr.risk_recheck = False
                ip_addr.save()
                return not soft
            else:
                ip_addr.risk_detected = False
                ip_addr.risk_recheck = False
                ip_addr.save()
                return False
        except:
            print(traceback.format_exc())
            try:
                ip=requests.get('https://api.antideo.com/ip/health/' + ip_addr.ip_address + '&apiKey={}'.format(ANTIDEO_KEY))
                j = ip.json()
                if j and j['health']['toxic'] or j['health']['spam']:
                    ip_addr.risk_detected = True
                    ip_addr.risk_recheck = False
                    ip_addr.save()
                    return not soft
                else:
                    ip_addr.risk_detected = False
                    ip_addr.risk_recheck = False
                    ip_addr.save()
                    return False
            except:
                try:
                    ip=requests.get('https://api.fraudguard.io/v2/ip/' + ip_addr.ip_address, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
                    ip_addr.fraudguard_data = ip
                    ip_addr.save()
                    j = ip.json()
                    if int(j['risk_level']) > RISK_LEVEL:
                        ip_addr.risk_detected = True
                        ip_addr.risk_recheck = False
                        ip_addr.save()
                        return not soft
                    else:
                        ip_addr.risk_detected = False
                        ip_addr.risk_recheck = False
                        ip_addr.save()
                        return False
                except:
                    print(traceback.format_exc())
                    return not soft
            print(traceback.format_exc())
            return not soft
    except:
        print(traceback.format_exc())
        return not soft
    return not soft
    return False

def check_raw_ip_risk(ip_address, soft=False, dummy=True, guard=True):
    if ip_in_range(ip_address): return False
    from security.models import UserIpAddress
    ip_address, createdUserIpAddress.objects.get_or_create(user=None, ip_address=ip_address)
    return check_ip_risk(ip_address, soft=soft)

def get_location(ip):
    try:
        response = requests.get('http://ipinfo.io/' + ip + '?token=490ce4335d8800').json()
        city = response['city']
        region = response['region']
        country = response['country']
        org = response['org']
        return '{}, {}, {} - {}'.format(city, region, country, org)
    except: return ''

def get_vivokey_response(nfc_id):
    from django.conf import settings
    data = {'signature': nfc_id}
    headers = {'Content-Type': 'application/json', 'X-API-VIVOKEY': settings.VIVOKEY_KEY}
    resp = requests.post('https://auth.vivokey.com/validate', json.dumps(data), headers=headers)
    print(resp.text)
    out = resp.json()
    if out['result'] == 'success' and out['token']: return out['token']
    return False
