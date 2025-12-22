from django.shortcuts import render
from project.models import *

# Create your views here.
def home(request):

    return render(request,'index.html')

from datetime import date as _date


def booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mail = request.POST.get('mail')
        mobile = request.POST.get('mobile')
        date_str = request.POST.get('date')

        # basic server-side validation
        if not name or not mail or not mobile or not date_str:
            return render(request, 'index.html', {'error': 'All fields are required.'})

        try:
            appt_date = _date.fromisoformat(date_str)
        except Exception:
            return render(request, 'index.html', {'error': 'Invalid date format.'})

        if appt_date < _date.today():
            return render(request, 'index.html', {'error': 'Appointment date must be today or later.'})

        bookings.objects.create(Name=name, mail=mail, mobile=mobile, appointment_date=appt_date)
        return render(request, 'index.html', {'success': 'Appointment booked successfully!'})
    
    puli = bookings.objects.all()
    context = {"BookApp": puli}
    return render(request, 'index.html', context)