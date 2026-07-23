from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta, datetime, date
from calendar import monthcalendar, month_name
from .models import Booking
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator

def booking_calendar(request, name):
    """Main booking calendar view with full month display"""
    today = timezone.now().date()
    
    # Get month and year from query parameters
    current_month = int(request.GET.get('month', today.month))
    current_year = int(request.GET.get('year', today.year))
    
    # Validate month and year
    if current_month < 1:
        current_month = 12
        current_year -= 1
    elif current_month > 12:
        current_month = 1
        current_year += 1
    
    # Ensure we can't go to past months
    if current_year < today.year or (current_year == today.year and current_month < today.month):
        current_month = today.month
        current_year = today.year
    
    # Get calendar for the selected month
    calendar_days = monthcalendar(current_year, current_month)
    
    # Create date objects for each day
    days_data = []
    for week in calendar_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                day_date = date(current_year, current_month, day)
                is_past = day_date < today
                week_data.append({
                    'day': day,
                    'date': day_date.strftime('%Y-%m-%d'),
                    'is_past': is_past,
                    'is_today': day_date == today,
                })
        days_data.append(week_data)
    
    # Generate list of available months (current and next 11 months)
    available_months = []
    for i in range(12):
        future_date = today + timedelta(days=30*i)
        available_months.append({
            'month': future_date.month,
            'year': future_date.year,
            'display': future_date.strftime('%B %Y'),
        })
    from django.contrib.auth.models import User
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(User, profile__name=name)
    context = {
        'calendar_days': days_data,
        'current_month': current_month,
        'current_year': current_year,
        'month_name': month_name[current_month],
        'today': today,
        'available_months': available_months,
        'weekday_headers': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'booking_user': user,
        'full': True,
    }
    return render(request, 'booking/calendar.html', context)


@require_http_methods(["GET"])
def get_available_times(request):
    """Get available time slots for a selected date via AJAX"""
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'error': 'Date not provided'}, status=400)
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        available_slots = Booking.get_available_slots(selected_date)
        booked_times = Booking.get_booked_times(selected_date)
        booked_times_str = [t.strftime('%H:%M') for t in booked_times]
        
        return JsonResponse({
            'available_slots': available_slots,
            'booked_times': booked_times_str,
            'date': date_str,
        })
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

@require_http_methods(["POST"])
def create_booking(request):
    from django.contrib.auth.models import User
    from django.shortcuts import get_object_or_404
    """Create a new booking"""
    date_str = request.POST.get('date')
    time_str = request.POST.get('time')
    customer_name = request.POST.get('customer_name')
    customer_email = request.POST.get('customer_email')
    phone = request.POST.get('phone')
    notes = request.POST.get('notes')
    username = request.POST.get('username')
    
    try:
        # Validate inputs
        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)
        if not time_str:
            return JsonResponse({'error': 'Time is required'}, status=400)
        if not customer_name:
            return JsonResponse({'error': 'Customer name is required'}, status=400)
        if not customer_email:
            return JsonResponse({'error': 'Customer email is required'}, status=400)
        
        # Parse date and time safely
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        try:
            start_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid time format. Use HH:MM'}, status=400)
        
        today = timezone.now().date()
        current_time = timezone.now().time()
        result_datetime = datetime.combine(datetime.today(), start_time) + timedelta(hours=1)
        end_time = result_datetime.time()
        d = selected_date
        from zoneinfo import ZoneInfo
        t = start_time
        from django.conf import settings
        location = settings.TIME_ZONE

        # 2. Combine and apply location info
        dt_naive = datetime.combine(d, t)
        dt_aware = dt_naive.replace(tzinfo=ZoneInfo(location))

        
        # Check if date is in the past
        if selected_date < today:
            return JsonResponse({'error': 'Cannot book appointments for past dates.'}, status=400)
        
        # Check if time is in the past (for today's bookings)
        if selected_date == today and start_time < current_time:
            return JsonResponse({'error': 'Cannot book appointments for past times.'}, status=400)
        

        vendor_user = get_object_or_404(User, profile__name=username)
        e = customer_email
        from users.username_generator import generate_username as get_random_username
        from django.utils.crypto import get_random_string
        from security.apis import get_client_ip
        from security.apis import check_raw_ip_risk
        from django.contrib.auth.models import User
        from email_validator import validate_email
        valid = validate_email(e, check_deliverability=True)
        us = User.objects.filter(email=e).last()
        from security.apis import check_raw_ip_risk
        ip = get_client_ip(request)
        safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
        if valid and (not us) and safe:
            user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
            if not hasattr(user, 'profile'):
                user.profile.finished_signup = False
                user.profile.save()
            send_verification_email(user)
        elif not valid: HttpResponse('Invalid or undeliverable email, please check the email and try again')
        elif not safe: HttpResponse('You are using a risky IP address, and your contact request has been denied.')
        us = User.objects.filter(email=e).last()

        booking = Booking.objects.create(
            title=f"Booking for {customer_name or 'Guest'}",
            date=selected_date,
            user=vendor_user,
            client=us,
            start_time=start_time,
            end_time=end_time,
            is_booked=True,
            customer_name=customer_name,
            customer_email=customer_email,
            phone=phone,
            notes=notes,
        )
        from events.models import Event
        event = Event.objects.create(title='Meeting with {}'.format(customer_name), start_time=dt_aware, end_time=(dt_aware + timedelta(hours=1)))
        event.update_description_link(vendor_user)
        calendar_url = event.get_calendar_url()
        link = event.link
        from users.email import send_html_email
        from users.email import send_email
        send_html_email(us, 'Thank you for booking a session with {}'.format(vendor_user.profile.name), 'Hello {},\nYour booking with {} starts on {}. You can use this link to add the event to your calendar. <a href="{}">Add to Calendar</a> Use this link to join the meeting: <a href="{}">Join Meeting</a>'.format(customer_name, vendor_user.profile.name, dt_aware.strftime("%A, %b %d, %Y at %H:%M:%S"), calendar_url, event.link) + '. Thank you for choosing ' + settings.SITE_NAME + ' and see you with us.')
        send_html_email(vendor_user, 'You have a new booking, {}'.format(vendor_user.profile.name), 'Hello {}, Your booking with {} starts on {}. You can use this link to add the event to your calendar. <a href="{}">Add to Calendar</a> Use this link to join the meeting: <a href="{}">Join Meeting</a>'.format(vendor_user.profile.name, customer_name, dt_aware.strftime("%A, %b %d, %Y at %H:%M:%S"), calendar_url, event.link) + '.')

        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'message': f'Booking confirmed for {selected_date} at {time_str}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def booked_times_list(request, name):
    """Display all booked appointments with filtering and search"""
    from django.contrib.auth.models import User
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(User, profile__name=name)
    if user != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    today = timezone.now().date()
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')  # all, upcoming, past
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-date')  # -date, date, -start_time, start_time, customer_name
    month_filter = request.GET.get('month', '')
    
    # Base queryset - only booked appointments
    bookings = Booking.objects.filter(is_booked=True, user=user)
    
    # Apply status filter
    if status_filter == 'upcoming':
        bookings = bookings.filter(date__gte=today)
    elif status_filter == 'past':
        bookings = bookings.filter(date__lt=today)
    
    # Apply search filter
    if search_query:
        bookings = bookings.filter(
            models.Q(customer_name__icontains=search_query) |
            models.Q(customer_email__icontains=search_query) |
            models.Q(phone__icontains=search_query) |
            models.Q(title__icontains=search_query)
        )
    
    # Apply month filter
    if month_filter:
        try:
            month_date = datetime.strptime(month_filter, '%Y-%m').date()
            bookings = bookings.filter(
                date__year=month_date.year,
                date__month=month_date.month
            )
        except ValueError:
            pass
    
    # Apply sorting
    bookings = bookings.order_by(sort_by)
    
    # Calculate stats
    total_bookings = bookings.count()
    upcoming_bookings = Booking.objects.filter(user=user, is_booked=True, date__gte=today).count()
    past_bookings = Booking.objects.filter(user=user, is_booked=True, date__lt=today).count()
    today_bookings = Booking.objects.filter(user=user, is_booked=True, date=today).count()
    
    # Pagination
    paginator = Paginator(bookings, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available months for filter
    available_months = Booking.objects.filter(user=user, is_booked=True).dates('date', 'month', order='DESC')
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'total_bookings': total_bookings,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'today_bookings': today_bookings,
        'today': today,
        'status_filter': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'month_filter': month_filter,
        'available_months': available_months,
        'booking_user': user,
    }
    
    return render(request, 'booking/booked_times_list.html', context)

@login_required
def booking_detail(request, booking_id):
    """Display detailed view of a single booking"""
    booking = Booking.objects.get(id=booking_id)
    
    context = {
        'booking': booking,
    }
    return render(request, 'booking/booking_detail.html', context)

@login_required
def booking_stats(request):
    """Display booking statistics and analytics"""
    today = timezone.now().date()
    
    # Get statistics
    total_booked = Booking.objects.filter(is_booked=True).count()
    total_slots = Booking.objects.count()
    occupancy_rate = (total_booked / total_slots * 100) if total_slots > 0 else 0
    
    upcoming_count = Booking.objects.filter(is_booked=True, date__gte=today).count()
    past_count = Booking.objects.filter(is_booked=True, date__lt=today).count()
    
    # Bookings by month (last 6 months)
    bookings_by_month = []
    for i in range(6):
        month_date = today - timedelta(days=30*i)
        count = Booking.objects.filter(
            is_booked=True,
            date__year=month_date.year,
            date__month=month_date.month
        ).count()
        bookings_by_month.append({
            'month': month_date.strftime('%B %Y'),
            'count': count,
        })
    
    bookings_by_month.reverse()
    
    # Bookings by hour
    bookings_by_hour = {}
    for booking in Booking.objects.filter(is_booked=True):
        hour = booking.start_time.strftime('%H:00')
        bookings_by_hour[hour] = bookings_by_hour.get(hour, 0) + 1
    
    # Most booked days
    from django.db.models import Count
    most_booked_days = Booking.objects.filter(is_booked=True).values('date').annotate(
        count=Count('date')
    ).order_by('-count')[:5]
    
    context = {
        'total_booked': total_booked,
        'total_slots': total_slots,
        'occupancy_rate': round(occupancy_rate, 1),
        'upcoming_count': upcoming_count,
        'past_count': past_count,
        'bookings_by_month': bookings_by_month,
        'bookings_by_hour': dict(sorted(bookings_by_hour.items())),
        'most_booked_days': most_booked_days,
    }
    
    return render(request, 'booking/booking_stats.html', context)
