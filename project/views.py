from django.shortcuts import render, get_object_or_404
from project.models import *

# Create your views here.
def home(request):

    return render(request,'index.html')

from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from datetime import date as _date, datetime
from django.core import signing
import io
import json

"""def booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mail = request.POST.get('mail')
        mobile = request.POST.get('mobile')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        # basic server-side validation
        if not name or not mail or not mobile or not date_str or not time_str:
            payload = {'success': False, 'error': 'All fields are required.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        try:
            appt_date = _date.fromisoformat(date_str)
        except Exception:
            payload = {'success': False, 'error': 'Invalid date format.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        if appt_date < _date.today():
            payload = {'success': False, 'error': 'Appointment date must be today or later.', 'errors': {'date': 'Appointment date must be today or later.'}}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        # Check if time slot is available (30-minute buffer)
        from datetime import time as datetime_time
        try:
            time_obj = datetime_time.fromisoformat(time_str)
        except Exception:
            payload = {'success': False, 'error': 'Invalid time format.', 'errors': {'time': 'Invalid time format.'}}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse(payload)
            return render(request, 'index.html', payload)
        
        # Create a temporary booking object to check availability
        temp_booking = bookings(Name=name, mail=mail, mobile=mobile, appointment_date=appt_date, time=time_obj)
        if not temp_booking.is_time_available(appt_date, time_obj):
            payload = {'success': False, 'error': 'This time slot is not available. Please choose another time (30-minute gap required).', 'errors': {'time': 'Time slot not available. Choose another time.'}}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        bookings.objects.create(Name=name, mail=mail, mobile=mobile, appointment_date=appt_date, time=time_obj)
        payload = {'success': True, 'message': 'Appointment booked successfully!'}
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse(payload)
        return render(request, 'index.html', payload)
    
    puli = bookings.objects.all()
    context = {"BookApp": puli}
    return render(request, 'index.html', context)"""

TIME_SLOTS = [
    "09:00 AM","09:15 AM","09:30 AM","09:45 AM",
    "10:00 AM","10:15 AM","10:30 AM","10:45 AM",
    "11:00 AM","11:15 AM","11:30 AM","11:45 AM",
    "02:00 PM","02:15 PM","02:30 PM","02:45 PM",
    "03:00 PM","03:15 PM","03:30 PM","03:45 PM",
    "04:00 PM","04:15 PM","04:30 PM","04:45 PM",
]

def booking(request):

    if request.method == 'POST':
        name = request.POST.get('name')
        mail = request.POST.get('mail')
        mobile = request.POST.get('mobile')
        date_str = request.POST.get('date')
        slot_str = request.POST.get('time_slot')

        # basic validation
        if not name or not mail or not mobile or not date_str or not slot_str:
            payload = {'success': False, 'error': 'All fields are required.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        try:
            appt_date = _date.fromisoformat(date_str)
        except Exception:
            payload = {'success': False, 'error': 'Invalid date format.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        if appt_date < _date.today():
            payload = {'success': False, 'error': 'Appointment date must be today or later.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        # Convert slot string to time object
        try:
            time_obj = datetime.strptime(slot_str, "%I:%M %p").time()
        except Exception:
            payload = {'success': False, 'error': 'Invalid time slot.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        # Check if this specific slot is already booked for this date
        existing_booking = bookings.objects.filter(
            appointment_date=appt_date,
            time=time_obj,
            status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
        ).exists()

        if existing_booking:
            payload = {
                'success': False,
                'error': 'This time slot is already booked. Please choose another slot.'
            }
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'index.html', payload)

        # Save booking
        bookings.objects.create(
            Name=name,
            mail=mail,
            mobile=mobile,
            appointment_date=appt_date,
            time=time_obj
        )

        payload = {'success': True, 'message': 'Appointment booked successfully!'}
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(payload)

        return render(request, 'index.html', payload)

    # GET: show booked slots for today
    today = _date.today()
    booked_today = bookings.objects.filter(
        appointment_date=today,
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    ).values_list('time', flat=True)
    
    # Convert time objects to 12-hour format strings for comparison
    booked_slots = []
    for t in booked_today:
        booked_slots.append(datetime.combine(_date.min, t).strftime("%I:%M %p"))
    
    # Get current system time
    current_time = datetime.now().strftime("%I:%M %p")
    
    puli = bookings.objects.all()
    context = {
        "BookApp": puli,
        "time_slots": TIME_SLOTS,
        "booked_slots": booked_slots,
        "current_time": current_time
    }
    return render(request, 'index.html', context)



# QR image endpoint (signed token required)
def booking_qr(request, pk):
    token = request.GET.get('token')
    if not token:
        return HttpResponseForbidden('Missing token')
    signer = signing.Signer()
    try:
        value = signer.unsign(token)
    except signing.BadSignature:
        return HttpResponseForbidden('Invalid token')
    if str(pk) != str(value):
        return HttpResponseForbidden('Token does not match')
    b = get_object_or_404(bookings, pk=pk)
    try:
        img_bytes = b.generate_qr_bytes(include_url=False)
    except Exception as e:
        return HttpResponse(f'Error generating QR: {e}', content_type='text/plain')
    return HttpResponse(img_bytes, content_type='image/png')


def get_booked_slots(request):
    """API endpoint to get booked slots for a specific date."""
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)
    
    try:
        appt_date = _date.fromisoformat(date_str)
    except Exception:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get all booked slots for this date (both pending and accepted)
    booked_times = bookings.objects.filter(
        appointment_date=appt_date,
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    ).values_list('time', flat=True)
    
    # Convert to 12-hour format strings
    booked_slots = []
    for t in booked_times:
        booked_slots.append(datetime.combine(_date.min, t).strftime("%I:%M %p"))
    
    # Get current system time
    current_time = datetime.now().strftime("%I:%M %p")
    is_today = appt_date == _date.today()
    
    return JsonResponse({
        'date': date_str,
        'booked_slots': booked_slots,
        'available_slots': [s for s in TIME_SLOTS if s not in booked_slots],
        'current_time': current_time,
        'is_today': is_today
    })