import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.contrib.contenttypes.models import ContentType
from simple_history.models import HistoricalRecords

from django.forms import model_to_dict

def undelete_all_objects(model):
    historical_model = model.history.model
    deleted_objects = historical_model.objects.filter(history_type='-')
    print(len(deleted_objects))
    for deleted_object in deleted_objects:
        print(deleted_object)
        d = deleted_object.instance
        d.pk = None
        d.save()

from feed.models import Post
undelete_all_objects(Post)
