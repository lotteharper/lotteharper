import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
import glob
from django.conf import settings
fileList = glob.glob(str(os.path.join(settings.BASE_DIR, '*TEMP_MPY_wvf_snd.mp3*')), recursive=True)
for file in fileList:
    try:
        os.remove(file)
    except OSError:
        print("Error while deleting file")
