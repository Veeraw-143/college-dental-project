import io
import json
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Import qrcode and PIL at module level to ensure they're available
try:
    import qrcode
    from PIL import Image
except ImportError as e:
    logger.error('Failed to import qrcode or PIL: %s. Please install them with: pip install qrcode[pil] pillow', e)
    qrcode = None


# ============= NEW MODELS =============

class Doctor(models.Model):
    DAY_CHOICES = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ]
    
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='doctors/', null=True, blank=True, help_text='Doctor profile photo')
    is_active = models.BooleanField(default=True)
    availability_days = models.CharField(
        max_length=50,
        default='Mon,Tue,Wed,Thu,Fri,Sat',
        help_text='Comma-separated days (Mon,Tue,Wed,Thu,Fri,Sat,Sun)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.specialization}"
    
    def get_available_days(self):
        """Return list of available days for this doctor"""
        return [day.strip() for day in self.availability_days.split(',')]
    
    def is_available_on_day(self, day_name):
        """Check if doctor is available on a specific day (e.g., 'Mon', 'Tue')"""
        return day_name in self.get_available_days()


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_minutes = models.IntegerField(default=30)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['name']

    def __str__(self):
        return self.name


class OTPVerification(models.Model):
    email = models.EmailField(null=True, blank=True)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.email}"

    def is_valid(self):
        """Check if OTP is still valid (not expired, verified, and attempts < 5)"""
        return (
            not self.is_verified
            and self.attempts < 5
            and timezone.now() < self.expires_at
        )

    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at


# ============= ORIGINAL MODELS =============

class bookings(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    mail = models.EmailField()
    mobile = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^[0-9]{10}$', message='Enter a valid 10-digit phone number')]
    )
    appointment_date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields
    preferred_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.Name} - {self.appointment_date} {self.get_time_12hr()}"

    def generate_qr_bytes(self, include_url=True):
        """Generate a PNG image (bytes) for this booking's QR code.
        The QR encodes the direct URL to the greeting card.
        """
        if qrcode is None:
            raise RuntimeError('qrcode and pillow packages are required to generate QR codes (pip install qrcode[pil] pillow)')
        
        signer = signing.Signer()
        token = signer.sign(str(self.pk))
        
        # Encode the direct URL in QR code for mobile scanning
        site = getattr(settings, 'SITE_URL', None)
        if site:
            path = reverse('booking_qr', args=[self.pk])
            qr_url = site.rstrip('/') + f'{path}?token={token}'
        else:
            path = reverse('booking_qr', args=[self.pk])
            qr_url = f'http://127.0.0.1:8000{path}?token={token}'
        
        # Encode URL directly in QR so mobile scanner opens it automatically
        img = qrcode.make(qr_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue()

    def send_admin_notification(self, request=None):
        """Send notification email to admin about new booking."""
        subject = f'New Appointment Request - {self.Name} on {self.appointment_date}'
        message = (
            f'New Appointment Booking Received:\n\n'
            f'Patient Name: {self.Name}\n'
            f'Email: {self.mail}\n'
            f'Phone: {self.mobile}\n'
            f'Appointment Date: {self.appointment_date}\n'
            f'Appointment Time: {self.get_time_12hr()}\n\n'
            f'Please review and accept/reject this booking in the admin panel.\n\n'
            f'Surabi Dental Care Admin'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pulipandi8158@gmail.com')
        admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pulipandi8158@gmail.com')
        to = [admin_email]

        try:
            email = EmailMessage(subject=subject, body=message, from_email=from_email, to=to)
            sent = email.send(fail_silently=False)
            logger.info('Sent admin notification for booking %s (patient: %s)', self.pk, self.Name)
        except Exception as e:
            logger.exception('Failed to send admin notification: %s', e)
            raise

    def send_qr_and_notify(self, request=None, sms_enabled=False):
        """Send the QR code to the user's email and optionally SMS (if configured).
        This method is safe to call multiple times and will raise on unrecoverable errors.
        """
        # Prepare email
        subject = 'Your appointment is confirmed — Surabi Dental Care'
        message = f'Hello {self.Name},\n\nYour appointment on {self.appointment_date} at {self.time} has been accepted. Attached is a QR code for your appointment.\n\nThank you,\nSurabi Dental Care Team'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pulipandi8158@gmail.com')
        # Ensure we have a valid recipient
        recipient = (self.mail or '').strip()
        if not recipient:
            logger.error('Attempted to send appointment email but booking %s has no email address', self.pk)
            if request is not None:
                try:
                    messages.error(request, f'Cannot send email for booking {self.pk}: no email address provided')
                except Exception:
                    pass
            raise ValueError('Booking has no email address')
        to = [recipient]

        # Generate QR bytes (include URL if SITE_URL configured)
        try:
            qr_bytes = self.generate_qr_bytes(include_url=True)
        except Exception as e:
            logger.exception('Failed to generate QR code: %s', e)
            raise

        # Send email with attached QR
        try:
            email = EmailMessage(subject=subject, body=message, from_email=from_email, to=to)
            email.attach(f'appointment_{self.pk}.png', qr_bytes, 'image/png')
            sent = email.send(fail_silently=False)
            logger.info('Sent appointment QR to email %s (booking id %s) - send() returned: %s', self.mail, self.pk, sent)

            # If a request object is provided, add an admin message that clarifies how the email was delivered
            backend = getattr(settings, 'EMAIL_BACKEND', '')
            if 'console' in backend:
                logger.info('Console email backend is configured; email was printed to the server console')
                if request is not None:
                    try:
                        messages.info(request, f'Email for booking {self.pk} was printed to the server console (console email backend in use).')
                    except Exception:
                        pass
            else:
                if request is not None:
                    try:
                        messages.success(request, f'Email for booking {self.pk} was sent via configured email backend.')
                    except Exception:
                        pass
        except Exception as e:
            logger.exception('Failed to send appointment email: %s', e)
            # If request provided, show a helpful admin error
            if request is not None:
                try:
                    messages.error(request, f'Failed to send appointment email for booking {self.pk}: {e}')
                except Exception:
                    pass
            raise

        # Optionally send SMS if Twilio is configured and sms_enabled True
        if sms_enabled:
            twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            twilio_from = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            if twilio_sid and twilio_token and twilio_from:
                try:
                    from twilio.rest import Client
                    client = Client(twilio_sid, twilio_token)
                    body = f"Your SmileCare appointment on {self.appointment_date} is confirmed. Check your email for the QR code."
                    # If SITE_URL available, include a short URL to the QR
                    site = getattr(settings, 'SITE_URL', None)
                    signer = signing.Signer()
                    token = signer.sign(self.pk)
                    if site:
                        path = reverse('booking_qr', args=[self.pk])
                        body += ' View QR: ' + site.rstrip('/') + f'{path}?token={token}'
                    client.messages.create(body=body, from_=twilio_from, to=self.mobile)
                    logger.info('Sent appointment SMS to %s (booking id %s)', self.mobile, self.pk)
                except Exception as e:
                    logger.exception('Failed to send SMS via Twilio: %s', e)
                    # Do not raise; email was already sent
            else:
                logger.debug('Twilio not configured; skipping SMS send for booking %s', self.pk)

    def is_time_available(self, appointment_date, time, buffer_minutes=30):
        """Check if a time slot is available (no bookings within buffer_minutes before/after)."""
        from django.db.models import Q
        from datetime import time as datetime_time
        
        time_obj = time if isinstance(time, type(self.time)) else time
        start_buffer = (time_obj.hour * 60 + time_obj.minute) - buffer_minutes
        end_buffer = (time_obj.hour * 60 + time_obj.minute) + buffer_minutes
        
        start_time = datetime_time(start_buffer // 60, start_buffer % 60)
        end_time = datetime_time(min(23, end_buffer // 60), end_buffer % 60 if end_buffer // 60 <= 23 else 59)
        
        conflicting = bookings.objects.filter(
            appointment_date=appointment_date,
            status__in=[bookings.STATUS_PENDING, bookings.STATUS_ACCEPTED]
        ).filter(
            Q(time__gte=start_time) & Q(time__lte=end_time)
        )
        
        return not conflicting.exists()
    
    def get_time_12hr(self):
        """Return time in 12-hour format with AM/PM."""
        if not self.time:
            return ''
        return self.time.strftime('%I:%M %p')

    def send_rejection_notification(self, request=None, reason: str | None = None):
        """Send a rejection email to the user notifying them their booking was rejected."""
        subject = 'Your appointment request — Surabi Dental Care'
        reason_text = f" Reason: {reason}" if reason else ''
        message = (
            f'Hello {self.Name},\n\n'
            f'We regret to inform you that your appointment on {self.appointment_date} has been rejected.{reason_text}\n\n'
            'If you would like to reschedule, please contact us or submit a new request.\n\n'
            'Thank you,\nSurabi Dental Care Team'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pulipandi8158@gmail.com')
        recipient = (self.mail or '').strip()
        if not recipient:
            logger.error('Attempted to send rejection email but booking %s has no email address', self.pk)
            if request is not None:
                try:
                    messages.error(request, f'Cannot send rejection email for booking {self.pk}: no email address provided')
                except Exception:
                    pass
            raise ValueError('Booking has no email address')
        to = [recipient]

        try:
            email = EmailMessage(subject=subject, body=message, from_email=from_email, to=to)
            sent = email.send(fail_silently=False)
            logger.info('Sent rejection email to %s (booking id %s) - send() returned: %s', self.mail, self.pk, sent)
            backend = getattr(settings, 'EMAIL_BACKEND', '')
            if 'console' in backend:
                logger.info('Console email backend is configured; email was printed to the server console')
                if request is not None:
                    try:
                        messages.info(request, f'Rejection email for booking {self.pk} was printed to the server console (console email backend in use).')
                    except Exception:
                        pass
            else:
                if request is not None:
                    try:
                        messages.success(request, f'Rejection email for booking {self.pk} was sent via configured email backend.')
                    except Exception:
                        pass
        except Exception as e:
            logger.exception('Failed to send rejection email: %s', e)
            if request is not None:
                try:
                    messages.error(request, f'Failed to send rejection email for booking {self.pk}: {e}')
                except Exception:
                    pass
            raise

    def send_reminder_notification(self, request=None):
        """Send a reminder email to the user 1 day before their appointment."""
        if not self.appointment_date or not self.time:
            logger.warning('Cannot send reminder for booking %s: missing date or time', self.pk)
            return
        
        subject = f'Appointment Reminder — Surabi Dental Care on {self.appointment_date}'
        message = (
            f'Hello {self.Name},\n\n'
            f'This is a friendly reminder about your upcoming appointment at Surabi Dental Care.\n\n'
            f'Appointment Details:\n'
            f'Date: {self.appointment_date}\n'
            f'Time: {self.get_time_12hr()}\n'
            f'Doctor: {self.preferred_doctor.name if self.preferred_doctor else "Not specified"}\n'
            f'Service: {self.preferred_service.name if self.preferred_service else "Not specified"}\n\n'
            f'Please arrive 10 minutes early. If you need to reschedule or cancel, please contact us as soon as possible.\n\n'
            f'Thank you,\nSurabi Dental Care Team'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pulipandi8158@gmail.com')
        recipient = (self.mail or '').strip()
        if not recipient:
            logger.error('Cannot send reminder for booking %s: no email address', self.pk)
            raise ValueError('Booking has no email address')
        
        to = [recipient]
        try:
            email = EmailMessage(subject=subject, body=message, from_email=from_email, to=to)
            sent = email.send(fail_silently=False)
            logger.info('Sent reminder email to %s (booking id %s)', self.mail, self.pk)
        except Exception as e:
            logger.exception('Failed to send reminder email: %s', e)
            raise


# ============= FEEDBACK MODEL =============

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(default='')
    message = models.TextField(max_length=500)
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# ============= EXCEL SYNC MODEL =============

class ExcelSync(models.Model):
    """Track Excel and database synchronization status"""
    
    MODEL_CHOICES = [
        ('Doctor', 'Doctor'),
        ('Service', 'Service'),
        ('bookings', 'Bookings'),
        ('Feedback', 'Feedback'),
        ('OTPVerification', 'OTP Verification'),
    ]
    
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    last_exported = models.DateTimeField(null=True, blank=True, help_text='Last time data was exported to Excel')
    last_imported = models.DateTimeField(null=True, blank=True, help_text='Last time data was imported from Excel')
    last_synced = models.DateTimeField(auto_now=True, help_text='Last sync check time')
    excel_file_path = models.CharField(max_length=255, blank=True, help_text='Path to the Excel file')
    record_count = models.IntegerField(default=0, help_text='Number of records in Excel')
    sync_enabled = models.BooleanField(default=True, help_text='Enable automatic sync for this model')
    last_error = models.TextField(blank=True, help_text='Last error message if any')
    
    class Meta:
        verbose_name = 'Excel Sync'
        verbose_name_plural = 'Excel Sync Status'
        unique_together = ('model_name',)
        ordering = ['model_name']
    
    def __str__(self):
        return f"{self.model_name} - Last synced: {self.last_synced.strftime('%Y-%m-%d %H:%M') if self.last_synced else 'Never'}"
    
    def mark_exported(self, filepath, record_count):
        """Mark model as exported"""
        self.last_exported = timezone.now()
        self.excel_file_path = filepath
        self.record_count = record_count
        self.last_error = ''
        self.save()
    
    def mark_imported(self, record_count):
        """Mark model as imported"""
        self.last_imported = timezone.now()
        self.record_count = record_count
        self.last_error = ''
        self.save()
    
    def mark_error(self, error_message):
        """Mark sync error"""
        self.last_error = error_message
        self.save()


