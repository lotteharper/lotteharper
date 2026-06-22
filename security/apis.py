import logging
import ipaddress
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

from .models import UserIpAddress

logger = logging.getLogger(__name__)

HACKERGUARDIAN_RANGES = []  # e.g. ['64.39.96.0/20', '139.87.112.0/23']
RISK_LEVEL = 1


def get_client_ip(request) -> Optional[str]:
    """
    Returns client IP. Prefer REMOTE_ADDR unless behind trusted proxy setup.
    If using django-ipware or SECURE_PROXY_SSL_HEADER patterns, adapt accordingly.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # First IP is original client in standard proxy chain format.
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def ip_in_range(ip_addr: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_addr)
    except ValueError:
        return False

    for cidr in HACKERGUARDIAN_RANGES:
        try:
            if ip_obj in ipaddress.ip_network(cidr):
                return True
        except ValueError:
            logger.warning("Invalid CIDR in HACKERGUARDIAN_RANGES: %s", cidr)
    return False


def get_ip_version(ip_string: str) -> Optional[str]:
    try:
        ip_obj = ipaddress.ip_address(ip_string)
        return "IPv4" if ip_obj.version == 4 else "IPv6"
    except ValueError:
        return None


def _set_risk(ip_addr: UserIpAddress, detected: bool) -> None:
    ip_addr.risk_detected = detected
    ip_addr.risk_recheck = False
    ip_addr.save(update_fields=["risk_detected", "risk_recheck"])


def check_ip_risk(ip_addr: UserIpAddress, soft: bool = False, dummy: bool = False) -> bool:
    """
    Returns True when request should be blocked (unless soft=True, then only marks risk).
    """
    if dummy:
        return False

    if not ip_addr.ip_address:
        return not soft

    if ip_in_range(ip_addr.ip_address):
        return False

    # 1) Local IPQualityScore DB
    try:
        from IPQualityScore.DBReader import DBReader

        version = get_ip_version(ip_addr.ip_address)
        if version:
            db_path = str(settings.BASE_DIR / f"security/IPQualityScore-IP-Reputation-Database-{version}.ipqs")
            record = DBReader(db_path).Fetch(ip_addr.ip_address)

            if any([
                record.IsBlacklisted(),
                record.IsTOR(),
                record.IsBot(),
                record.RecentAbuse(),
            ]):
                _set_risk(ip_addr, True)
                return not soft
    except Exception:
        logger.exception("IPQualityScore lookup failed for %s", ip_addr.ip_address)

    # 2) VirusTotal
    try:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_addr.ip_address}"
        headers = {"accept": "application/json", "x-apikey": settings.VIRUSTOTAL_API_KEY}
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        result = response.json()

        stats = (
            result.get("data", {})
            .get("attributes", {})
            .get("last_analysis_stats", {})
        )
        malicious = int(stats.get("malicious", 0))
        suspicious = int(stats.get("suspicious", 0))

        if malicious > 0 or suspicious > 0:
            _set_risk(ip_addr, True)
            return not soft
    except Exception:
        logger.exception("VirusTotal lookup failed for %s", ip_addr.ip_address)

    # 3) AbuseIPDB (FIXED: now reachable)
    try:
        headers = {
            "Key": settings.ABUSEIPDB_KEY,
            "Accept": "application/json",
        }
        params = {
            "ipAddress": ip_addr.ip_address,
            "maxAgeInDays": 90,
            "verbose": True,
        }
        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers=headers,
            params=params,
            timeout=8,
        )
        response.raise_for_status()
        result = response.json()

        score = int(result.get("data", {}).get("abuseConfidenceScore", 0))
        if score > 0:
            _set_risk(ip_addr, True)
            return not soft
    except Exception:
        logger.exception("AbuseIPDB lookup failed for %s", ip_addr.ip_address)

    # 4) Antideo
    try:
        # Use query params instead of string concat
        response = requests.get(
            f"https://api.antideo.com/ip/health/{ip_addr.ip_address}",
            params={"apiKey": settings.ANTIDEO_KEY},
            timeout=8,
        )
        response.raise_for_status()
        j = response.json()
        health = j.get("health", {})
        if bool(health.get("toxic")) or bool(health.get("spam")):
            _set_risk(ip_addr, True)
            return not soft
    except Exception:
        logger.exception("Antideo lookup failed for %s", ip_addr.ip_address)

    # 5) FraudGuard
    try:
        response = requests.get(
            f"https://api.fraudguard.io/v2/ip/{ip_addr.ip_address}",
            verify=True,
            auth=HTTPBasicAuth(settings.FRAUDGUARD_USER, settings.FRAUDGUARD_SECRET),
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        # Keep serializable content, not Response object
        ip_addr.fraudguard_data = data
        ip_addr.save(update_fields=["fraudguard_data"])

        risk_level = int(data.get("risk_level", 0))
        if risk_level > RISK_LEVEL:
            _set_risk(ip_addr, True)
            return not soft
    except Exception:
        logger.exception("FraudGuard lookup failed for %s", ip_addr.ip_address)

    _set_risk(ip_addr, False)
    return False


def check_raw_ip_risk(ip_address: str, soft: bool = False, dummy: bool = True, guard: bool = True) -> bool:
    if not guard:
        return False
    if ip_in_range(ip_address):
        return False

    ip_obj, _ = UserIpAddress.objects.get_or_create(user=None, ip_address=ip_address)
    return check_ip_risk(ip_obj, soft=soft, dummy=dummy)


def get_location(ip: str) -> str:
    try:
        response = requests.get(
            f"https://ipinfo.io/{ip}",
            params={"token": "490ce4335d8800"},
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        city = data.get("city", "")
        region = data.get("region", "")
        country = data.get("country", "")
        org = data.get("org", "")
        return f"{city}, {region}, {country} - {org}".strip(" ,-")
    except Exception:
        logger.exception("ipinfo lookup failed for %s", ip)
        return ""


def get_vivokey_response(nfc_id: str):
    data = {"signature": nfc_id}
    headers = {
        "Content-Type": "application/json",
        "X-API-VIVOKEY": settings.VIVOKEY_KEY,
    }
    try:
        resp = requests.post(
            "https://auth.vivokey.com/validate",
            json=data,   # requests serializes safely
            headers=headers,
            timeout=8,
        )
        resp.raise_for_status()
        out = resp.json()
        if out.get("result") == "success" and out.get("token"):
            return out["token"]
    except Exception:
        logger.exception("Vivokey validation failed")
    return False