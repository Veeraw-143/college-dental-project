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
