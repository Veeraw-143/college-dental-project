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

logger = logging.getLogger(__name__)

try:
    import qrcode
    from PIL import Image
except Exception:
    qrcode = None

# Create your models here.
class bookings(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    mail = models.EmailField()
    mobile = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?[0-9]{10,12}$', message='Enter a valid phone number')]
    )
    appointment_date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
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
        The QR encodes a signed token containing the booking id and a small summary.
        """
        if qrcode is None:
            raise RuntimeError('qrcode and pillow packages are required to generate QR codes (pip install qrcode[pil] pillow)')
        payload = {
            'id': self.pk,
            'name': self.Name,
            'date': str(self.appointment_date)
        }
        signer = signing.Signer()
        token = signer.sign(str(self.pk))
        if include_url:
            site = getattr(settings, 'SITE_URL', None)
            if site:
                path = reverse('booking_qr', args=[self.pk])
                payload['qr_url'] = site.rstrip('/') + f'{path}?token={token}'
            else:
                payload['token'] = token
        # encode payload as JSON inside QR
        data = json.dumps(payload)
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue()

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
                messages.error(request, f'Cannot send email for booking {self.pk}: no email address provided')
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
                    messages.info(request, f'Email for booking {self.pk} was printed to the server console (console email backend in use).')
            else:
                if request is not None:
                    messages.success(request, f'Email for booking {self.pk} was sent via configured email backend.')
        except Exception as e:
            logger.exception('Failed to send appointment email: %s', e)
            # If request provided, show a helpful admin error
            if request is not None:
                messages.error(request, f'Failed to send appointment email for booking {self.pk}: {e}')
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
                messages.error(request, f'Cannot send rejection email for booking {self.pk}: no email address provided')
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
                    messages.info(request, f'Rejection email for booking {self.pk} was printed to the server console (console email backend in use).')
            else:
                if request is not None:
                    messages.success(request, f'Rejection email for booking {self.pk} was sent via configured email backend.')
        except Exception as e:
            logger.exception('Failed to send rejection email: %s', e)
            if request is not None:
                messages.error(request, f'Failed to send rejection email for booking {self.pk}: {e}')
            raise

