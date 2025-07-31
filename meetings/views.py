import uuid
from django.shortcuts import render, redirect, get_object_or_404
from .models import Meeting

def meeting(request, meeting_id=None):
    """
    Render the meeting page with the specified meeting_id.
    If no meeting_id is provided, create a new Meeting and redirect.
    """
    if not meeting_id:
        meeting = Meeting.objects.create(created_by=request.user)
        return redirect('meetings:meeting', meeting_id=str(meeting.identifier))

    meeting = get_object_or_404(Meeting, identifier=meeting_id)
    # You can use request.user.username if authenticated, else generate a random user ID
    user_id = request.user.id if request.user.is_authenticated else str(uuid.uuid4())[:8]
    return render(request, "meetings/meeting.html", {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "full": True,
    })
