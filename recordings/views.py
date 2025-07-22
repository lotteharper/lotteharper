from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified, minor_identity_verified
from barcode.tests import minor_document_scanned
from django.views.decorators.csrf import csrf_exempt

@login_required
#@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def recordings(request, username):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    from barcode.tests import minor_document_scanned as document_scanned
    model = User.objects.get(profile__name=username)
    if (not model in request.user.profile.subscriptions.all()) and not model == request.user and not request.user.profile.vendor:
        messages.warning(request, 'You need to follow {} before you can see their interactive feed.'.format(username))
        return redirect(reverse('feed:follow', kwargs={'username': username}))
    page = 1
    if(request.GET.get('page', '') != ''):
        page = int(request.GET.get('page', ''))
    recordings = None
    private_recordings = None
    from django.db.models import Count
    recordings_annotated = VideoRecording.objects.annotate(num_frames=Count('frames'))
    if model == request.user and request.GET.get('all'):
        recordings = recordings_annotated.filter(user__profile__name=username, processed=True, safe=not minor_document_scanned(request.user), num_frames__gte=9).exclude(youtube_embed='').order_by('-last_frame')
    elif model == request.user and request.GET.get('camera'):
        recordings = recordings_annotated.filter(user__profile__name=username, processed=True, camera=request.GET.get('camera'), safe=not minor_document_scanned(request.user), num_frames__gte=9).order_by('-last_frame')
    else:
        recordings = recordings_annotated.filter(user__profile__name=username, processed=True, camera='private', safe=not minor_document_scanned(request.user), num_frames__gte=9).order_by('-last_frame')
    private_recordings = recordings_annotated.filter(user__profile__name=username, processed=True, recipient=request.user, safe=not document_scanned(request.user), num_frames__gte=9).exclude(youtube_embed='').order_by('-last_frame')
    recordings = list(chain(private_recordings, recordings))
    p = Paginator(recordings, 10)
    if page > p.num_pages or page < 1:
        messages.warning(request, "The page you requested, " + str(page) + ", does not exist. You have been redirected to the first page.")
        page = 1
    return render(request, 'recordings/recordings.html', {
        'title': 'Recordings',
        'recordings': p.page(page),
        'count': p.count,
        'page_obj': p.get_page(page),
        'model': model
    })

@login_required
@user_passes_test(minor_identity_verified, login_url='/verify/', redirect_field_name='next')
def recording(request, uuid):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from live.models import VideoRecording
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.views.generic import DeleteView
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
    from vendors.tests import is_vendor
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    recordings = VideoRecording.objects.filter(uuid=uuid, processed=True)
    private_recordings = VideoRecording.objects.filter(uuid=uuid, processed=True, recipient=request.user)
    recording = list(chain(private_recordings, recordings))[0]
    if not recording and uuid == 'last':
        recording = VideoRecording.objects.filter(user=request.user).last()
    return render(request, 'recordings/recording.html', {'title': 'Recording', 'recording': recording})

@login_required
@user_passes_test(minor_identity_verified, login_url='/verify/', redirect_field_name='next')
def recording_frame(request, uuid):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from live.models import VideoRecording
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.views.generic import DeleteView
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
    from vendors.tests import is_vendor
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    recording = get_object_or_404(VideoRecording, uuid=uuid)
    model = recording.user
    if (not model in request.user.profile.subscriptions.all()) and not model == request.user and not request.user.profile.vendor:
        messages.warning(request, 'You need to follow {} before you can see their interactive feed.'.format(username))
        return redirect(reverse('feed:follow', kwargs={'username': username}))
    frame = recording.get_file_url()
    return render(request, 'recordings/frame.html', {'title': 'Recording', 'frame': frame})

def idle_recording(username):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from live.models import VideoRecording
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.views.generic import DeleteView
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
    from vendors.tests import is_vendor
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    recordings = VideoRecording.objects.filter(user__username=username, interactive='idle', camera='private')
    recording = recordings[math.random(0, recordings.count()-1)]
    return recording

def idle_frame(username):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from live.models import VideoRecording
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.views.generic import DeleteView
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
    from vendors.tests import is_vendor
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    recording = idle_recording(username)
    frame = recording.frames.all()[math.random(0, recording.frames.count()-1)]
    return frame

@login_required
@user_passes_test(minor_identity_verified, login_url='/verify/', redirect_field_name='next')
def recording_idle(request, username):
    from live.models import VideoRecording
    from django.shortcuts import render
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    from live.models import VideoRecording
    from django.core.paginator import Paginator
    from .forms import RecordingInteractiveForm
    from interactive.forms import ChoicesCreateForm
    from interactive.models import Choices
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.conf import settings
    from live.models import get_file_path
    import os
    from django.views.generic import DeleteView
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
    from vendors.tests import is_vendor
    from django.core.exceptions import PermissionDenied
    from security.security import fraud_detect
    from itertools import chain
    model = User.objects.get(profile__name=username)
    if (not model in request.user.profile.subscriptions.all()) and not model == request.user:
        messages.warning(request, 'You need to follow {} before you can see their interactive feed.'.format(username))
        return redirect(reverse('feed:follow', kwargs={'username': username}))
    recording = idle_recording(username)
    return HttpResponse(recording.uuid)


from live.models import VideoRecording
from django.views.generic import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class RecordingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = VideoRecording
    success_url = '/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        recording = self.get_object()
        if pediatric_identity_verified(self.request.user) and is_vendor(self.request.user) and ((not recording.camera == 'private' and self.request.user == recording.user) or (self.request.user.is_superuser and not recording.user.is_superuser)) and not fraud_detect(self.request, True):
            return True
        return False
