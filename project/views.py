from django.shortcuts import render, get_object_or_404
from project.models import *
import logging
import random
import string
from django.utils import timezone
from datetime import date as _date, datetime, timedelta
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core import signing
import io
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

TIME_SLOTS = [
    "09:00 AM", "09:15 AM", "09:30 AM", "09:45 AM",
    "10:00 AM", "10:15 AM", "10:30 AM", "10:45 AM",
    "11:00 AM", "11:15 AM", "11:30 AM", "11:45 AM",
    "02:00 PM", "02:15 PM", "02:30 PM", "02:45 PM",
    "03:00 PM", "03:15 PM", "03:30 PM", "03:45 PM",
    "04:00 PM", "04:15 PM", "04:30 PM", "04:45 PM",
]


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def is_sunday(date_obj):
    """Check if a date is Sunday (weekday 6)"""
    return date_obj.weekday() == 6


# Create your views here.
def home(request):
    doctors = Doctor.objects.filter(is_active=True)
    services = Service.objects.filter(is_active=True)
    feedbacks = Feedback.objects.filter(is_active=True).order_by('-created_at')[:3]
    context = {
        'doctors': doctors,
        'services': services,
        'feedbacks': feedbacks,
    }
    return render(request, 'home.html', context)


def services_view(request):
    """Display all services"""
    services = Service.objects.filter(is_active=True)
    context = {
        'services': services,
    }
    return render(request, 'services.html', context)


def doctors_view(request):
    """Display all doctors"""
    doctors = Doctor.objects.filter(is_active=True)
    context = {
        'doctors': doctors,
    }
    return render(request, 'doctors.html', context)


def contact_view(request):
    """Display contact page"""
    return render(request, 'contact.html', {})


def feedback_view(request):
    """Display feedback page"""
    feedbacks = Feedback.objects.filter(is_active=True).order_by('-created_at')[:6]
    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'feedback.html', context)


def send_otp(request):
    """Send OTP to email address"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Validate email
        if not email or '@' not in email:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a valid email address'
            })
        
        try:
            # Generate OTP
            otp_code = generate_otp()
            
            # Create or update OTP record
            otp_obj, created = OTPVerification.objects.get_or_create(
                email=email,
                defaults={
                    'otp_code': otp_code,
                    'expires_at': timezone.now() + timedelta(minutes=10)
                }
            )
            
            if not created:
                # Update existing OTP
                otp_obj.otp_code = otp_code
                otp_obj.attempts = 0
                otp_obj.is_verified = False
                otp_obj.expires_at = timezone.now() + timedelta(minutes=10)
                otp_obj.save()
            
            # Send OTP via email
            from django.core.mail import send_mail
            subject = "Your OTP for Surabi Dental Clinic Appointment"
            message = f"""
Hello,

Your OTP for verifying your email at Surabi Dental Clinic is:

{otp_code}

This OTP is valid for 10 minutes. Do not share this with anyone.

If you didn't request this, please ignore this email.

Best regards,
Surabi Dental Care Team
            """
            
            # Send OTP to user email
            send_mail(
                subject,
                message,
                'noreply@surabidental.com',
                [email],
                fail_silently=False,
            )
            
            # Also print to console for development/testing
            print(f"\n{'='*50}")
            print(f"OTP for {email}: {otp_code}")
            print(f"{'='*50}\n")
            logger.info(f'OTP sent to email: {email}. OTP: {otp_code}')
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {email}. Check your email for the OTP code.'
            })
        
        except Exception as e:
            logger.error(f'Failed to send OTP: {str(e)}')
            print(f"OTP Error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to send OTP: {str(e)}'
            })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def verify_otp(request):
    """Verify OTP sent to email"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        otp_code = request.POST.get('otp', '').strip()
        
        if not email or not otp_code:
            return JsonResponse({
                'success': False,
                'error': 'Email and OTP are required'
            })
        
        try:
            otp_obj = OTPVerification.objects.get(email=email)
            
            # Check if OTP is expired
            if timezone.now() > otp_obj.expires_at:
                return JsonResponse({
                    'success': False,
                    'error': 'OTP has expired. Please request a new one.'
                })
            
            # Check attempts
            if otp_obj.attempts >= 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Too many failed attempts. Please request a new OTP.'
                })
            
            # Check OTP
            if otp_obj.otp_code == otp_code:
                otp_obj.is_verified = True
                otp_obj.save()
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified successfully!'
                })
            else:
                otp_obj.attempts += 1
                otp_obj.save()
                remaining = 5 - otp_obj.attempts
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid OTP. {remaining} attempts remaining.'
                })
        
        except OTPVerification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No OTP record found. Please request OTP first.'
            })
        
        except Exception as e:
            logger.error(f'Error verifying OTP: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': f'Error verifying OTP: {str(e)}'
            })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def booking(request):
    """Handle appointment booking"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        mail = request.POST.get('mail', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        date_str = request.POST.get('date', '').strip()
        slot_str = request.POST.get('time_slot', '').strip()
        doctor_id = request.POST.get('doctor_id', '').strip()
        service_id = request.POST.get('service_id', '').strip()
        otp_verified = request.POST.get('otp_verified', 'false').lower() == 'true'

        # Validation
        errors = {}
        
        if not name or len(name) < 2:
            errors['name'] = 'Please enter a valid name'
        
        if not mail or '@' not in mail:
            errors['mail'] = 'Please enter a valid email'
        
        # Phone validation - 10 digits only
        if not mobile or not mobile.isdigit() or len(mobile) != 10:
            errors['mobile'] = 'Please enter a valid 10-digit phone number'
        
        if not date_str:
            errors['date'] = 'Please select a date'
        
        if not slot_str:
            errors['time_slot'] = 'Please select a time slot'
        
        if not otp_verified:
            errors['otp'] = 'Please verify your phone number with OTP'
        
        if errors:
            payload = {'success': False, 'errors': errors}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        try:
            appt_date = _date.fromisoformat(date_str)
        except Exception:
            payload = {'success': False, 'error': 'Invalid date format'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        # Check if date is Sunday
        if is_sunday(appt_date):
            payload = {'success': False, 'error': 'Appointments cannot be booked on Sundays. Please choose another date.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        # Check if date is in the past
        if appt_date < _date.today():
            payload = {'success': False, 'error': 'Appointment date must be today or later'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        # Convert slot to time object
        try:
            time_obj = datetime.strptime(slot_str, "%I:%M %p").time()
        except Exception:
            payload = {'success': False, 'error': 'Invalid time slot'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        # Check if slot is available
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
            return render(request, 'home.html', payload)
        
        # Save booking
        try:
            preferred_doctor = None
            preferred_service = None
            
            if doctor_id:
                try:
                    preferred_doctor = Doctor.objects.get(pk=int(doctor_id))
                except (Doctor.DoesNotExist, ValueError):
                    pass
            
            if service_id:
                try:
                    preferred_service = Service.objects.get(pk=int(service_id))
                except (Service.DoesNotExist, ValueError):
                    pass
            
            new_booking = bookings.objects.create(
                Name=name,
                mail=mail,
                mobile=mobile,
                appointment_date=appt_date,
                time=time_obj,
                preferred_doctor=preferred_doctor,
                preferred_service=preferred_service,
                otp_verified=True
            )
            
            # Send admin notification
            try:
                new_booking.send_admin_notification(request=request)
            except Exception as e:
                logger.warning(f'Failed to send admin notification for booking {new_booking.pk}: {e}')
        
        except Exception as e:
            logger.error(f'Failed to create booking: {e}')
            payload = {'success': False, 'error': 'Failed to create appointment. Please try again.'}
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(payload)
            return render(request, 'home.html', payload)
        
        payload = {
            'success': True,
            'message': 'Appointment booked successfully! Admin will confirm your booking soon.',
            'booking_id': new_booking.pk
        }
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(payload)
        
        return render(request, 'home.html', payload)
    
    # GET: Provide data for form
    doctors = Doctor.objects.filter(is_active=True)
    services = Service.objects.filter(is_active=True)
    today = _date.today()
    
    # Get booked slots for today
    booked_today = bookings.objects.filter(
        appointment_date=today,
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    ).values_list('time', flat=True)
    
    booked_slots = [datetime.combine(_date.min, t).strftime("%I:%M %p") for t in booked_today]
    current_time = datetime.now().strftime("%I:%M %p")
    
    context = {
        "time_slots": TIME_SLOTS,
        "booked_slots": booked_slots,
        "current_time": current_time,
        "doctors": doctors,
        "services": services,
    }
    return render(request, 'home.html', context)


def get_doctors_and_services(request):
    """API endpoint to get available doctors and services"""
    doctors = Doctor.objects.filter(is_active=True).values('id', 'name', 'specialization')
    services = Service.objects.filter(is_active=True).values('id', 'name', 'description', 'duration_minutes', 'cost')
    
    return JsonResponse({
        'doctors': list(doctors),
        'services': list(services)
    })


def get_booked_slots(request):
    """API endpoint to get booked slots for a specific date"""
    date_str = request.GET.get('date')
    doctor_id = request.GET.get('doctor_id')  # Optional: filter by doctor
    
    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)
    
    try:
        appt_date = _date.fromisoformat(date_str)
    except Exception:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Check if date is Sunday
    if is_sunday(appt_date):
        return JsonResponse({
            'date': date_str,
            'booked_slots': TIME_SLOTS,  # All slots blocked
            'available_slots': [],
            'current_time': datetime.now().strftime("%I:%M %p"),
            'is_today': appt_date == _date.today(),
            'is_sunday': True,
            'message': 'Clinic is closed on Sundays'
        })

    # Check doctor availability on the selected day
    day_name = appt_date.strftime('%a')  # Mon, Tue, Wed, etc.
    doctor_not_available = False
    doctor_message = ''
    
    if doctor_id:
        try:
            doctor = Doctor.objects.get(id=doctor_id, is_active=True)
            if not doctor.is_available_on_day(day_name):
                doctor_not_available = True
                doctor_message = f'{doctor.name} is not available on {day_name}. Available days: {doctor.availability_days}'
                return JsonResponse({
                    'date': date_str,
                    'booked_slots': TIME_SLOTS,  # All slots blocked
                    'available_slots': [],
                    'current_time': datetime.now().strftime("%I:%M %p"),
                    'is_today': appt_date == _date.today(),
                    'is_sunday': False,
                    'doctor_not_available': True,
                    'message': doctor_message
                })
        except Doctor.DoesNotExist:
            pass
    
    # Get booked slots
    booked_times = bookings.objects.filter(
        appointment_date=appt_date,
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    )
    
    # Filter by doctor if specified
    if doctor_id:
        booked_times = booked_times.filter(preferred_doctor_id=doctor_id)
    
    booked_times = booked_times.values_list('time', flat=True)
    booked_slots = [datetime.combine(_date.min, t).strftime("%I:%M %p") for t in booked_times]
    current_time = datetime.now().strftime("%I:%M %p")
    is_today = appt_date == _date.today()
    
    return JsonResponse({
        'date': date_str,
        'booked_slots': booked_slots,
        'available_slots': [s for s in TIME_SLOTS if s not in booked_slots],
        'current_time': current_time,
        'is_today': is_today,
        'is_sunday': False
    })


# Management command functions for automatic updates
def update_expired_appointments():
    """Update status of appointments that have passed their time (should be called by management command)"""
    from datetime import datetime as dt
    now = dt.now()
    
    # Find appointments that are in the past and still pending/accepted
    expired_bookings = bookings.objects.filter(
        appointment_date__lt=_date.today(),
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    ).update(status=bookings.STATUS_COMPLETED)
    
    # Also check today's appointments where time has passed
    today_expired = bookings.objects.filter(
        appointment_date=_date.today(),
        time__lt=now.time(),
        status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
    ).update(status=bookings.STATUS_COMPLETED)
    
    return expired_bookings + today_expired


def send_reminder_emails():
    """Send reminder emails for appointments tomorrow (should be called by management command)"""
    tomorrow = _date.today() + timedelta(days=1)
    
    # Get all confirmed appointments for tomorrow that haven't sent reminder yet
    appointments_tomorrow = bookings.objects.filter(
        appointment_date=tomorrow,
        status=bookings.STATUS_ACCEPTED,
        reminder_sent=False
    )
    
    sent_count = 0
    failed_count = 0
    
    for appointment in appointments_tomorrow:
        try:
            appointment.send_reminder_notification()
            appointment.reminder_sent = True
            appointment.save()
            sent_count += 1
            logger.info(f'Reminder email sent for booking {appointment.pk}')
        except Exception as e:
            logger.error(f'Failed to send reminder for booking {appointment.pk}: {e}')
            failed_count += 1
    
    return {'sent': sent_count, 'failed': failed_count}


# Greeting card view (signed token required)
def booking_qr(request, pk):
    try:
        token = request.GET.get('token')
        if not token:
            return HttpResponseForbidden('Error: Missing security token. Cannot access greeting card.')
        
        signer = signing.Signer()
        try:
            value = signer.unsign(token)
        except signing.BadSignature:
            logger.warning(f'Invalid token attempt for booking {pk}')
            return HttpResponseForbidden('Error: Invalid security token. Cannot access greeting card.')
        
        if str(pk) != str(value):
            logger.warning(f'Token mismatch for booking {pk}')
            return HttpResponseForbidden('Error: Security token does not match. Cannot access greeting card.')
        
        b = get_object_or_404(bookings, pk=pk)
        
        # Prepare context with booking details
        context = {
            'booking': b,
            'name': b.Name,
            'date': b.appointment_date,
            'time': b.get_time_12hr(),
            'clinic_location': 'Surabi Dental Care, Clinic Address',
            'clinic_phone': '+91-XXXXXXXXXX',
            'booking_id': b.pk,
        }
        
        return render(request, 'greeting_card.html', context)
    except Exception as e:
        logger.error(f'Error in booking_qr view: {e}')
        return HttpResponse('Error: Something went wrong. Please try again.', status=500)


def manage_appointments(request):
    """Management view for checking appointment status (for patients)"""
    context = {}
    return render(request, 'manage_appointments.html', context)


def admin_dashboard(request):
    """Admin dashboard view"""
    from django.contrib.auth.decorators import login_required, user_passes_test
    from django.shortcuts import redirect
    
    # If user is not authenticated, redirect to Django admin login
    if not request.user.is_authenticated:
        return redirect('/admin-panel/login/?next=/admin/')
    
    # If user is not staff, deny access
    if not request.user.is_staff:
        return HttpResponseForbidden('You do not have permission to access this page.')
    
    context = {}
    return render(request, 'admin_dashboard.html', context)


def admin_stats_api(request):
    """API endpoint to get admin dashboard statistics"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        from django.db.models import Q, Count
        
        total_bookings = bookings.objects.count()
        total_doctors = Doctor.objects.filter(is_active=True).count()
        total_services = Service.objects.filter(is_active=True).count()
        pending_approvals = bookings.objects.filter(status='pending').count()
        
        # Get bookings by status for pie chart
        bookings_by_status = bookings.objects.values('status').annotate(count=Count('id')).order_by('status')
        
        # Get doctor-wise appointments count
        doctor_appointments = []
        for doctor in Doctor.objects.filter(is_active=True).order_by('name'):
            count = bookings.objects.filter(preferred_doctor=doctor).count()
            doctor_appointments.append({
                'doctor_name': doctor.name,
                'count': count
            })
        
        # Get monthly booking trend
        from django.db.models.functions import TruncMonth
        monthly_bookings = bookings.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        monthly_data = []
        for item in monthly_bookings:
            if item['month']:
                monthly_data.append({
                    'month': item['month'].strftime('%b %Y'),
                    'count': item['count']
                })
        
        return JsonResponse({
            'total_bookings': total_bookings,
            'total_doctors': total_doctors,
            'total_services': total_services,
            'pending_approvals': pending_approvals,
            'bookings_by_status': list(bookings_by_status),
            'doctor_appointments': doctor_appointments,
            'monthly_bookings': monthly_data,
        })
    except Exception as e:
        logger.error(f'Error in admin_stats_api: {e}')
        return JsonResponse({'error': str(e)}, status=500)
    
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required(login_url='/admin/login/')
def logout_view(request):
    """Logout view for admin panel"""
    
    
    logout(request)
    return redirect('/admin/login/')


# ============= CHATBOT VIEWS =============

class IntentDetector:
    """Intelligent intent detection for AI Assistant"""
    
    # Intent types
    INTENT_BOOK_APPOINTMENT = 'BOOK_APPOINTMENT'
    INTENT_VIEW_DOCTORS = 'VIEW_DOCTORS'
    INTENT_VIEW_SERVICES = 'VIEW_SERVICES'
    INTENT_SUBMIT_FEEDBACK = 'SUBMIT_FEEDBACK'
    INTENT_CONTACT_US = 'CONTACT_US'
    INTENT_GENERAL_FAQ = 'GENERAL_FAQ'
    
    # Keywords for intent detection
    INTENT_KEYWORDS = {
        INTENT_BOOK_APPOINTMENT: [
            'book', 'appointment', 'slot', 'schedule', 'booking', 'timing', 'time', 
            'date', 'when can i', 'want to book', 'get appointment', 'reserve', 'check slot'
        ],
        INTENT_VIEW_DOCTORS: [
            'doctor', 'dentist', 'specialist', 'team', 'staff', 'physician', 'who is',
            'show doctor', 'list doctor', 'available doctor', 'which doctor', 'meet doctor'
        ],
        INTENT_VIEW_SERVICES: [
            'service', 'treatment', 'procedure', 'cost', 'price', 'charge', 'fee',
            'how much', 'what service', 'available service', 'dental work', 'offer'
        ],
        INTENT_SUBMIT_FEEDBACK: [
            'feedback', 'review', 'rating', 'suggestion', 'compliment', 'complaint',
            'comment', 'opinion', 'experience', 'suggest'
        ],
        INTENT_CONTACT_US: [
            'contact', 'call', 'phone', 'whatsapp', 'emergency', 'urgent', 'help',
            'number', 'email', 'address', 'reach', 'get help'
        ]
    }
    
    # Multilingual responses for each intent
    INTENT_RESPONSES = {
        INTENT_BOOK_APPOINTMENT: {
            'en': "I'll help you book an appointment! 📅 You can schedule your visit by selecting a date, time, and preferred dentist. Our team will confirm your booking within 24 hours. Let's get you scheduled!",
            'ta': "உங்களுக்கு சந்திப்பு முன்பதிவு செய்ய உதவுவேன்! 📅 நீங்கள் ஒரு தேதி, நேரம் மற்றும் விரும்பிய பல் வைத்தியரைத் தேர்ந்தெடுத்து உங்கள் சந்திப்பைத் திட்டமிடலாம்.",
            'hi': "मैं आपकी अपॉइंटमेंट बुक करने में मदद करूंगा! 📅 आप एक तारीख, समय और पसंदीदा दंत चिकित्सक का चयन करके अपनी यात्रा का समय तय कर सकते हैं।"
        },
        INTENT_VIEW_DOCTORS: {
            'en': "Great! Let me show you our experienced team of dentists. 👨‍⚕️ Each specialist brings expertise in different areas of dental care. You can view their profiles and choose your preferred doctor for your appointment.",
            'ta': "멋진! எங்கள் அভிজ్ఞ பல் வைத்தியர்களின் குழுவைக் காட்ட விடுங்கள். 👨‍⚕️ ஒவ்வொரு நிபுணரும் பல் பராமரிப்பின் வெவ்வேறு பகுதிகளில் திறமை கொண்டுவருகிறார்.",
            'hi': "बढ़िया! मैं आपको हमारे अनुभवी दंत चिकित्सकों की टीम दिखाता हूं। 👨‍⚕️ प्रत्येक विशेषज्ञ दंत चिकित्सा के विभिन्न क्षेत्रों में विशेषज्ञता लाता है।"
        },
        INTENT_VIEW_SERVICES: {
            'en': "Perfect! Let me show you our comprehensive range of dental services. 🦷 We offer everything from general dentistry to specialized treatments. You'll find detailed information about each service including duration and cost.",
            'ta': "சரி! எங்கள் விரிவான பல் சेவைகளின் வரம்பைக் காட்ட விடுங்கள். 🦷 பொது பல் மருத்துவம் முதல் சிறப்புப் பிரிவு சிகிச்சை வரை எல்லாம் வழங்குகிறோம்.",
            'hi': "बिल्कुल! मैं आपको हमारी व्यापक दंत सेवाओं की श्रृंखला दिखाता हूं। 🦷 हम सामान्य दंत चिकित्सा से लेकर विशेष उपचार तक सब कुछ प्रदान करते हैं।"
        },
        INTENT_SUBMIT_FEEDBACK: {
            'en': "We'd love to hear from you! 💬 Your feedback helps us improve our services. Please share your experience, and we'll make sure our team receives your valuable input.",
            'ta': "நீங்கள் கூறுவதை நாங்கள் கேட்க விரும்புகிறோம்! 💬 உங்கள் கருத்து எங்கள் சேவைகளை மேம்படுத்த உதவுகிறது.",
            'hi': "हम आपसे सुनना पसंद करेंगे! 💬 आपकी प्रतिक्रिया हमारी सेवाओं को बेहतर बनाने में मदद करती है।"
        },
        INTENT_CONTACT_US: {
            'en': "Need to get in touch? 📞 You can reach us at +91-9123-456-789 or email pulipandi8158@gmail.com. Our team is here to help with any questions you have!",
            'ta': "நம்மைத் தொடர்பு கொள்ள வேண்டுமா? 📞 நீங்கள் +91-9123-456-789 இல் அல்லது pulipandi8158@gmail.com க்கு மின்னஞ்சல் மூலம் தொடர்பு கொள்ளலாம்.",
            'hi': "हमसे संपर्क करने की जरूरत है? 📞 आप +91-9123-456-789 पर कॉल कर सकते हैं या pulipandi8158@gmail.com पर ईमेल कर सकते हैं।"
        }
    }
    
    # Redirect URLs for each intent
    REDIRECT_URLS = {
        INTENT_BOOK_APPOINTMENT: '/',
        INTENT_VIEW_DOCTORS: '/doctors',
        INTENT_VIEW_SERVICES: '/services',
        INTENT_SUBMIT_FEEDBACK: '/feedback',
        INTENT_CONTACT_US: '/contact'
    }
    
    @staticmethod
    def detect_intent(user_message):
        """Detect user intent from message"""
        user_message_lower = user_message.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        
        for intent, keywords in IntentDetector.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in user_message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return the highest scoring intent, or GENERAL_FAQ if no match
        if intent_scores:
            detected_intent = max(intent_scores, key=intent_scores.get)
            return detected_intent
        
        return IntentDetector.INTENT_GENERAL_FAQ
    
    @staticmethod
    def get_response_for_intent(intent, language='en'):
        """Get response message for detected intent"""
        if intent in IntentDetector.INTENT_RESPONSES:
            responses = IntentDetector.INTENT_RESPONSES[intent]
            return responses.get(language, responses.get('en'))
        return None
    
    @staticmethod
    def get_redirect_url(intent):
        """Get redirect URL for detected intent"""
        return IntentDetector.REDIRECT_URLS.get(intent, None)


def simple_faq_search(user_message, language):
    """Intelligent FAQ search when Ollama is not available using similarity matching"""
    from difflib import SequenceMatcher
    
    # Default FAQs for all languages
    default_faqs = {
        'en': [
            {'q': 'how do i book an appointment', 'a': 'To book an appointment: 1) Visit our website 2) Select your preferred doctor and date 3) Choose a time slot 4) Enter your details 5) Verify your email with OTP 6) Confirm booking. You will receive a confirmation email.'},
            {'q': 'what are your clinic hours', 'a': 'Our clinic is open Monday to Saturday, 9:00 AM to 5:00 PM. We are closed on Sundays. Please contact us for holiday hours.'},
            {'q': 'do you have emergency services', 'a': 'Yes, we handle emergencies. Please call us immediately at +91-9123-456-789 for urgent dental issues.'},
            {'q': 'what services do you offer', 'a': 'We offer a wide range of dental services including General Dentistry, Orthodontics, Cosmetic Dentistry, Root Canal Treatment, Implants, and more.'},
            {'q': 'is parking available', 'a': 'Yes, we have dedicated parking space for our patients. Contact us for specific parking details.'},
            {'q': 'do you accept insurance', 'a': 'Yes, we accept various insurance plans. Please call us to confirm if your insurance is accepted.'},
            {'q': 'how long does an appointment take', 'a': 'Most appointments take 30-45 minutes depending on the treatment required. Emergency visits may be shorter.'},
            {'q': 'what should i bring for my first visit', 'a': 'Please bring your ID, insurance card, and any previous dental records if available. Arrive 10 minutes early.'},
        ],
        'ta': [
            {'q': 'நான் எப்படி சந்திப்பை முன்பதிவு செய்யலாம்', 'a': 'சந்திப்பைப் முன்பதிவு செய்ய: 1) எங்கள் இணையதளத்ைக் பார்க்கவும் 2) உங்கள் விரும்பிய வைத்தியர் மற்றும் தேதியைத் தேர்ந்தெடுக்கவும் 3) ஒரு நேர இடத்தைத் தேர்ந்தெடுக்கவும் 4) உங்கள் விவரங்களை உள்ளிடவும் 5) OTP உயர் உங்கள் மின்னஞ்சலை சரிபார்க்கவும் 6) முன்பதிவை உறுதிப்படுத்தவும்.'},
            {'q': 'உங்கள் சிகிச்சை சாலை நேரம் என்ன', 'a': 'எங்கள் சிகிச்சை சாலை திங்கட்கிழமை முதல் சனிக்கிழமை, காலை 9:00 மணி முதல் மாலை 5:00 மணி வரை திறந்திருக்கும். ஞாயிற்றுக்கிழமை மூடப்பட்டுள்ளது.'},
            {'q': 'உங்களுக்கு அவசர சேவைகள் உள்ளதா', 'a': 'ஆம், நாங்கள் அவசரகாலங்களைக் கையாளுகிறோம். அவசரமான பல் சிக்கல்களுக்கு +91-9123-456-789 குக் அழைக்கவும்.'},
            {'q': 'நீங்கள் என்ன சேவைகளை வழங்குகிறீர்கள்', 'a': 'நாங்கள் பொது பல் சிகிச்சை, பற்களை வரிசைப்படுத்துதல், அழகு பல் சிகிச்சை, ரூட் கால் சிகிச்சை, பொருத்துதல் மற்றும் பல வழங்குகிறோம்.'},
        ],
        'hi': [
            {'q': 'मैं अपॉइंटमेंट कैसे बुक करूं', 'a': 'अपॉइंटमेंट बुक करने के लिए: 1) हमारी वेबसाइट पर जाएं 2) अपने पसंदीदा डॉक्टर और तारीख चुनें 3) एक समय स्लॉट चुनें 4) अपना विवरण दर्ज करें 5) OTP से अपना ईमेल सत्यापित करें 6) बुकिंग की पुष्टि करें।'},
            {'q': 'आपके क्लिनिक के घंटे क्या हैं', 'a': 'हमारा क्लिनिक सोमवार से शनिवार, सुबह 9:00 से शाम 5:00 तक खुला है। हम रविवार को बंद हैं।'},
            {'q': 'क्या आपके पास आपातकालीन सेवाएं हैं', 'a': 'हां, हम आपात स्थिति को संभालते हैं। तत्काल दंत समस्याओं के लिए +91-9123-456-789 पर कॉल करें।'},
            {'q': 'आप कौन सी सेवाएं प्रदान करते हैं', 'a': 'हम सामान्य दंत चिकित्सा, ऑर्थोडॉन्टिक्स, कॉस्मेटिक दंत चिकित्सा, रूट कैनाल उपचार, इम्प्लांट और अधिक प्रदान करते हैं।'},
        ]
    }
    
    user_message_lower = user_message.lower()
    faqs = FAQ.objects.filter(language=language, is_active=True)
    
    best_match = None
    best_score = 0.3  # Minimum threshold for match
    
    # First try to match with database FAQs
    for faq in faqs:
        question_lower = faq.question.lower()
        similarity = SequenceMatcher(None, user_message_lower, question_lower).ratio()
        
        if similarity > best_score:
            best_score = similarity
            best_match = faq.answer
    
    # If database FAQs don't match well, try default FAQs
    if best_score < 0.5 and language in default_faqs:
        for faq_pair in default_faqs[language]:
            similarity = SequenceMatcher(None, user_message_lower, faq_pair['q']).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = faq_pair['a']
    
    # If we found a good match, return it
    if best_match:
        return best_match
    
    # Fallback: Provide helpful response based on common keywords
    keywords_responses = {
        'en': {
            'book|appointment|slot|timing|time': 'To book an appointment, visit our website and follow the booking form. Select your preferred doctor, date, and time slot. You\'ll need to verify your email with an OTP to complete the booking.',
            'doctor|specialist|dentist': 'We have experienced dentists specializing in various dental treatments. Visit our Doctors page to view our team or contact us at +91-9123-456-789.',
            'service|treatment|dental': 'We offer comprehensive dental services. Check our Services page or call us to learn more about specific treatments available.',
            'cost|price|charge|fee': 'For pricing information, please call us at +91-9123-456-789 or email pulipandi8158@gmail.com.',
            'hour|open|close|timing': 'We are open Monday to Saturday, 9 AM to 5 PM. Closed on Sundays. Call us for any queries.',
        },
        'ta': {
            'book|appointment|slot': 'சந்திப்பைப் முன்பதிவு செய்ய, எங்கள் இணையதளத்ைக் பார்க்கவும் மற்றும் முன்பதிவு படிவத்ைப் பூர்த்திசெய்யவும்.',
            'doctor|specialist': 'அভিজ்ञ பல் வைத்தியர் நம்மிடம் உள்ளனர். +91-9123-456-789 ல் தொலைபேசி செய்யவும்.',
            'service|treatment': 'விस్తృత பல் சேवा प्रदान करते हैं। আরও जानकारी के लिए আমাদের సేवา पাতा देखें।',
        },
        'hi': {
            'book|appointment|slot': 'अपॉइंटमेंट बुक करने के लिए हमारी वेबसाइट पर जाएं और फॉर्म भरें।',
            'doctor|specialist': 'हमारे पास अनुभवी डॉक्टर हैं। अधिक जानकारी के लिए +91-9123-456-789 पर कॉल करें।',
            'service|treatment': 'हम व्यापक दंत सेवाएं प्रदान करते हैं।',
        }
    }
    
    # Check keywords in user message
    if language in keywords_responses:
        for pattern, response in keywords_responses[language].items():
            if any(keyword in user_message_lower for keyword in pattern.split('|')):
                return response
    
    # Final fallback: Contact info
    contact_messages = {
        'en': 'Thank you for your question! I\'ll be happy to help. For more detailed information, please contact us at +91-9123-456-789 or email pulipandi8158@gmail.com',
        'ta': 'உங்கள் கேள்விக்கு நன்றி! மேலும் தகவலுக்கு, +91-9123-456-789 என்ற எண்ணில் தொலைபேசி செய்யவும் அல்லது pulipandi8158@gmail.com க்கு மின்னஞ்சல் அனுப்பவும்',
        'hi': 'आपके सवाल के लिए धन्यवाद! अधिक जानकारी के लिए कृपया +91-9123-456-789 पर कॉल करें या pulipandi8158@gmail.com पर ईमेल करें।'
    }
    return contact_messages.get(language, contact_messages['en'])


@csrf_exempt
def chatbot_message_api(request):
    """Enhanced AI Assistant with Intent Detection and Auto-Redirect"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method', 'success': False}, status=405)
    
    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'success': False}, status=400)
        
        user_message = data.get('message', '').strip()
        language = data.get('language', 'en').lower()  # en, ta, hi
        
        if not user_message:
            return JsonResponse({'error': 'Message is required', 'success': False}, status=400)
        
        # Validate language
        valid_languages = ['en', 'ta', 'hi']
        if language not in valid_languages:
            language = 'en'
        
        # ========== PHASE 1: INTENT DETECTION ==========
        detected_intent = IntentDetector.detect_intent(user_message)
        
        # ========== PHASE 2: ACTION-BASED INTENTS (with Redirect) ==========
        if detected_intent != IntentDetector.INTENT_GENERAL_FAQ:
            # Get response message for this intent
            intent_message = IntentDetector.get_response_for_intent(detected_intent, language)
            redirect_url = IntentDetector.get_redirect_url(detected_intent)
            
            if intent_message and redirect_url:
                return JsonResponse({
                    'success': True,
                    'message': intent_message,
                    'language': language,
                    'intent': detected_intent,
                    'action': 'redirect',
                    'redirect_url': redirect_url,
                    'auto_redirect_delay': 3000,  # 3 seconds
                    'mode': 'action'
                })
        
        # ========== PHASE 3: GENERAL FAQ (no redirect) ==========
        # Get language display name
        lang_display = {'en': 'English', 'ta': 'Tamil', 'hi': 'Hindi'}[language]
        
        # Build knowledge base context from FAQ and BookingTip models
        context_items = []
        
        # Get FAQs for the selected language
        faqs = FAQ.objects.filter(language=language, is_active=True).order_by('category', 'order')
        if faqs.exists():
            context_items.append(f"=== FREQUENTLY ASKED QUESTIONS ({lang_display}) ===\n")
            for faq in faqs:
                context_items.append(f"Q: {faq.question}\nA: {faq.answer}\n")
        
        # Get booking tips for the selected language
        tips = BookingTip.objects.filter(language=language, is_active=True).order_by('step_order')
        if tips.exists():
            context_items.append(f"\n=== HOW TO BOOK AN APPOINTMENT ===\n")
            for tip in tips:
                context_items.append(f"Step {tip.step_order}: {tip.title}\n{tip.description}\n")
        
        knowledge_base = "".join(context_items)
        
        # Try to use Ollama if available
        ollama_available = False
        try:
            # Build prompt for Ollama
            prompt = f"""You are a helpful customer service chatbot for Surabi Dental Care clinic. You assist patients with information about our services, appointments, and FAQ.

KNOWLEDGE BASE:
{knowledge_base}

Current language: {lang_display}
Patient question: {user_message}

Instructions:
1. Answer based ONLY on the knowledge base provided above.
2. Be concise and helpful (keep responses under 150 words).
3. Use the same language as the patient question.
4. If you don't know the answer, suggest they call us at +91-9123-456-789 or email pulipandi8158@gmail.com
5. Always maintain a professional and friendly tone.

Response:"""
            
            # Call Ollama API with shorter timeout
            ollama_response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.7,
                },
                timeout=15  # Reduced timeout
            )
            
            if ollama_response.status_code == 200:
                response_data = ollama_response.json()
                chatbot_response = response_data.get('response', '').strip()
                
                if chatbot_response:
                    ollama_available = True
                    return JsonResponse({
                        'success': True,
                        'message': chatbot_response,
                        'language': language,
                        'intent': IntentDetector.INTENT_GENERAL_FAQ,
                        'action': None,
                        'mode': 'ollama'
                    })
        
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logger.warning(f'Ollama service not available: {str(e)}, using fallback FAQ search')
        
        # ========== PHASE 4: INTELLIGENT FALLBACK FAQ SEARCH ==========
        if not ollama_available:
            try:
                fallback_response = simple_faq_search(user_message, language)
                return JsonResponse({
                    'success': True,
                    'message': fallback_response,
                    'language': language,
                    'intent': IntentDetector.INTENT_GENERAL_FAQ,
                    'action': None,
                    'mode': 'fallback_faq'
                })
            except Exception as e:
                logger.error(f'Fallback FAQ search failed: {str(e)}')
                
                # Final fallback: Contact info
                contact_messages = {
                    'en': 'Thank you for your question! Please contact us at +91-9123-456-789 or email pulipandi8158@gmail.com for assistance.',
                    'ta': 'உங்கள் கேள்விக்கு நன்றி! உதவிக்கு +91-9123-456-789 என்ற எண்ணில் தொலைபேசி செய்யவும் அல்லது pulipandi8158@gmail.com க்கு மின்னஞ்சல் அனுப்பவும்.',
                    'hi': 'आपके सवाल के लिए धन्यवाद! सहायता के लिए कृपया +91-9123-456-789 पर कॉल करें या pulipandi8158@gmail.com पर ईमेल करें।'
                }
                return JsonResponse({
                    'success': True,
                    'message': contact_messages.get(language, contact_messages['en']),
                    'language': language,
                    'intent': IntentDetector.INTENT_GENERAL_FAQ,
                    'action': None,
                    'mode': 'contact_fallback'
                })
    
    except Exception as e:
        logger.exception(f'Error in chatbot_message_api: {e}')
        return JsonResponse({
            'error': 'Internal chatbot error',
            'message': 'An error occurred. Please contact us directly: +91-9123-456-789',
            'success': False
        }, status=500)


def get_faq_list(request):
    """API endpoint to get all FAQs for a specific language"""
    language = request.GET.get('language', 'en').lower()
    
    valid_languages = ['en', 'ta', 'hi']
    if language not in valid_languages:
        language = 'en'
    
    faqs = FAQ.objects.filter(language=language, is_active=True).values(
        'id', 'question', 'answer', 'category', 'order'
    ).order_by('category', 'order')
    
    return JsonResponse({
        'language': language,
        'faqs': list(faqs)
    })


# ============= FEEDBACK VIEWS =============

def submit_feedback(request):
    """Handle feedback submission via AJAX"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        rating = request.POST.get('rating', '5').strip()
        
        # Validate input
        if not name or not email or not message:
            return JsonResponse({
                'success': False,
                'error': 'Please provide name, email, and feedback message'
            })
        
        if len(message) > 500:
            return JsonResponse({
                'success': False,
                'error': 'Feedback message is too long (max 500 characters)'
            })
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                rating = 5
        except (ValueError, TypeError):
            rating = 5
        
        try:
            # Create feedback entry
            feedback = Feedback.objects.create(
                name=name,
                email=email,
                message=message,
                rating=rating,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!',
                'feedback': {
                    'id': feedback.id,
                    'name': feedback.name,
                    'email': feedback.email,
                    'message': feedback.message,
                    'rating': feedback.rating,
                    'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=200)
        except Exception as e:
            logger.exception('Error creating feedback: %s', e)
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while submitting your feedback'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)


def get_all_feedback(request):
    """Get all active feedback entries for display"""
    try:
        feedbacks = Feedback.objects.filter(is_active=True).order_by('-created_at')
        feedback_list = [
            {
                'id': fb.id,
                'name': fb.name,
                'message': fb.message,
                'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for fb in feedbacks
        ]
        
        return JsonResponse({
            'success': True,
            'feedbacks': feedback_list
        })
    except Exception as e:
        logger.exception('Error retrieving feedback: %s', e)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while retrieving feedback'
        })
