from django.shortcuts import render
from project.models import *

# Create your views here.
def home(request):

    return render(request,'index.html')

from django.http import JsonResponse
from datetime import date as _date


def booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mail = request.POST.get('mail')
        mobile = request.POST.get('mobile')
        date_str = request.POST.get('date')

        # basic server-side validation
        if not name or not mail or not mobile or not date_str:
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

        bookings.objects.create(Name=name, mail=mail, mobile=mobile, appointment_date=appt_date)
        payload = {'success': True, 'message': 'Appointment booked successfully!'}
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse(payload)
        return render(request, 'index.html', payload)
    
    puli = bookings.objects.all()
    context = {"BookApp": puli}
    return render(request, 'index.html', context)