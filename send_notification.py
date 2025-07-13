import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from webpush import send_user_notification

print('Outbox: {}'.format(sys.argv[1]))

def send_notification(user):
    # Define the payload for your notification
    payload = {
        "head": "You have received a notification from the administrator.",
        "body": sys.argv[2],
        "icon": "/media/static/lips.png", # Optional: path to an icon for the notification
        "url": "https://glamgirlx.com" # Optional: URL to open when the notification is clicked
    }

    # Get the user object (e.g., the currently logged-in user)
    # Send the notification to the user
    # ttl (Time To Live) specifies how long the push server should store the notification if the user is offline.
    send_user_notification(user=user, payload=payload, ttl=1000)

    print('Success.')


from django.contrib.auth.models import User
from django.conf import settings
user = User.objects.filter(profile__name=sys.argv[1]).order_by('-profile__last_seen').first()
print('Sending to user {}'.format(str(user)))
send_notification(user)
