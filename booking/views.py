from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Booking

def booking_calendar(request):
    """Main booking calendar view"""
    today = timezone.now().date()
    next_30_days = [today + timedelta(days=i) for i in range(30)]
    
    context = {
        'dates': next_30_days,
        'today': today,
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
    """Create a new booking"""
    date_str = request.POST.get('date')
    time_str = request.POST.get('time')
    customer_name = request.POST.get('customer_name')
    customer_email = request.POST.get('customer_email')
    phone = request.POST.get('phone')
    notes = request.POST.get('notes')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(time_str, '%H:%M').time()
        end_time = (datetime.combine(selected_date, start_time) + timedelta(hours=1)).time()
        
        # Check if slot is already booked
        existing_booking = Booking.objects.filter(
            date=selected_date,
            start_time=start_time,
            is_booked=True
        ).exists()
        
        if existing_booking:
            return JsonResponse({'error': 'This time slot is already booked'}, status=400)
        
        booking = Booking.objects.create(
            title=f"Booking for {customer_name or 'Guest'}",
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            is_booked=True,
            customer_name=customer_name,
            customer_email=customer_email,
            phone=phone,
            notes=notes,
        )
        
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'message': f'Booking confirmed for {selected_date} at {time_str}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
