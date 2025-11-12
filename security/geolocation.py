import requests, json
from django.conf import settings

def get_country(latitude, longitude):
    if latitude != None and longitude != None:
        try:
            res = get_country_online(latitude, longitude)
            l, la = res
            print('{}, {} - coords'.format(l,la))
            if res: return res
        except:
            return get_country_offline(latitude, longitude)
        return get_country_offline(latitude, longitude)
    else: return None

def get_country_online(latitude, longitude):
    from geopy.geocoders import Nominatim
    """
    Retrieves the country name for given latitude and longitude coordinates.
    """
    from django.conf import settings
    geolocator = Nominatim(user_agent=settings.SITE_NAME) # Replace with your app name
    try:
        location = geolocator.reverse(f"{latitude}, {longitude}")
        if location and 'address' in location.raw and 'country' in location.raw['address']:
            return location.raw['address']['country']
        else:
            return None
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None

def get_country_offline(latitude, longitude):
    import reverse_geocode
    coords = [(latitude, longitude)]
    result = reverse_geocode.search(coords)
    if result:
        return result[0]['country']
    else:
        return None

def get_ip_location(ip):
    try:
        response = requests.get(f"http://api.ipstack.com/{ip}?access_key={settings.IPSTACK_GEOLOCATION_API_KEY}")
        result = response.json()
        return (result['latitude'], result['longitude'])
    except:
        try:
            response = requests.get('https://api.ipgeolocation.io/ipgeo?apiKey={}&ip={}'.format(settings.GEOLOCATION_API_KEY, ip))
            result = response.json()
            return (float(result['latitude']), float(result['longitude']))
        except:
            import traceback
            print(traceback.format_exc())
            try:
                import geocoder
                ip = geocoder.ip(ip)
                latlng = ip.latlng
                return (latlng[0], latlng[1])
            except: return (None, None)
