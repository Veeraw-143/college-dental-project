from django.shortcuts import render
from project.models import *

# Create your views here.
def home(request):

    return render(request,'index.html')

def booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mail = request.POST.get('mail')
        mobile = request.POST.get('mobile')
        bookings.objects.create(Name=name, mail=mail, mobile=mobile)
        return render(request, 'index.html', {'success': 'Appointment booked successfully!'})
    
    puli = bookings.objects.all()
    context = {"BookApp": puli}
    return render(request, 'index.html', context)