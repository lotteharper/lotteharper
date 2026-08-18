from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Case, When
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Shift
from .forms import PunchOutForm


# default max shift length (hours) — override in settings.py as TIMELOCK_MAX_SHIFT_HOURS
MAX_SHIFT_HOURS = getattr(settings, "TIMELOCK_MAX_SHIFT_HOURS", 12)


@login_required
def punch_in(request):
    """
    Create a new shift for the logged-in user if they do not have an active shift.
    """
    # expire any overly-long active shifts first
    active = Shift.objects.filter(user=request.user, end_time__isnull=True, expired=False)
    for s in active:
        s.expire_if_older_than(hours=MAX_SHIFT_HOURS)

    # after expiry pass, check again for an active shift
    still_active = Shift.objects.filter(user=request.user, end_time__isnull=True, expired=False).exists()
    if still_active:
        messages.error(request, "You already have an active shift. Punch out before punching in again.")
        return redirect("timeclock:shift_list")

    Shift.objects.create(user=request.user)
    messages.success(request, "Punched in.")
    return redirect("timeclock:shift_list")


@login_required
def punch_out(request):
    """
    Set end_time for the user's most recent active shift.
    """
    shift = Shift.objects.filter(user=request.user, end_time__isnull=True, expired=False).order_by("-start_time").first()
    if not shift:
        messages.error(request, "No active shift to punch out from.")
        return redirect("timeclock:shift_list")

    if request.method == "POST":
        form = PunchOutForm(request.POST)
        if form.is_valid():
            shift.end_time = timezone.now()
            shift.notes = form.cleaned_data.get("notes", "")
            shift.save(update_fields=["end_time", "notes", "updated_at"])
            messages.success(request, "Punched out.")
            return redirect("timeclock:shift_list")
    else:
        form = PunchOutForm()

    return render(request, "timeclock/punch_out.html", {"form": form, "shift": shift})


@login_required
def shift_list(request):
    """
    Show recent shifts for the user and highlight active/expired shifts.
    Active shifts older than MAX_SHIFT_HOURS will be auto-marked as expired on view.
    """
    active_qs = Shift.objects.filter(user=request.user, end_time__isnull=True, expired=False)
    for s in active_qs:
        s.expire_if_older_than(hours=MAX_SHIFT_HOURS)

    shifts = Shift.objects.filter(user=request.user).order_by("-start_time")[:100]
    return render(request, "timeclock/shift_list.html", {"shifts": shifts, "max_hours": MAX_SHIFT_HOURS})


@login_required
def monthly_summary(request):
    """
    Monthly totals for the logged-in user.
    Uses TruncMonth + Sum of (end_time - start_time) for closed shifts.
    Also returns recent months even if total is zero.
    """
    # only closed shifts provide reliable durations
    closed_shifts = Shift.objects.filter(user=request.user, end_time__isnull=False, expired=False)

    # expression: end_time - start_time
    duration_expr = ExpressionWrapper(F("end_time") - F("start_time"), output_field=DurationField())

    monthly_qs = (
        closed_shifts
        .annotate(month=TruncMonth("start_time"))
        .values("month")
        .annotate(total_duration=Sum(duration_expr))
        .order_by("-month")
    )

    # Normalize results to a list of tuples (month, total_seconds)
    history = []
    for item in monthly_qs:
        month = item["month"]
        total = item["total_duration"] or timedelta(0)
        # convert to seconds for easier rendering
        history.append({"month": month, "total_seconds": total.total_seconds()})

    return render(request, "timeclock/monthly_summary.html", {"history": history})
