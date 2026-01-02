from django.shortcuts import render, get_object_or_404
from project.models import *

# Create your views here.
def home(request):

    return render(request,'index.html')

from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from datetime import date as _date
from django.core import signing
import io
import json

def booking(request):
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