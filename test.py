print('This is a test script.')
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

import datetime

from security.models import UserIpAddress, Session
latlngs = []
from django.conf import settings
for ip in UserIpAddress.objects.all():
    if ip.latitude and ip.longitude: latlngs = latlngs + [(ip.latitude, ip.longitude)]
import numpy as np
from sklearn.cluster import DBSCAN
coords = np.array(latlngs)
# Haversine metric requires radians:
kms_per_radian = 6371.0088
epsilon = 50 / kms_per_radian # 50km radius

db = DBSCAN(eps=epsilon, min_samples=2, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
labels = db.labels_
groups = {}
for label, point in zip(labels, latlngs):
    groups.setdefault(label, []).append(point)

pts = []

for x in range(len(groups)-1):
    pts = pts + [groups[x][0]]

print(pts)
