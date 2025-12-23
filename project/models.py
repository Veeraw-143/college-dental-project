import io
import json
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.urls import reverse

logger = logging.getLogger(__name__)

try:
    import qrcode
    from PIL import Image
except Exception:
    qrcode = None

# Create your models here.
class bookings(models.Model):
    Name = models.CharField(max_length=50)
    mail = models.EmailField()
    mobile = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?[0-9]{7,15}$', message='Enter a valid phone number')]
    )
    appointment_date = models.DateField(null=True, blank=True)
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
        return self.Name

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
        token = signer.sign(self.pk)
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
        subject = 'Your appointment is confirmed — SmileCare'
        message = f'Hello {self.Name},\n\nYour appointment on {self.appointment_date} has been accepted. Attached is a QR code for your appointment.\n\nThank you,\nSmileCare Team'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@smilecare.example')
        to = [self.mail]

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
            email.send(fail_silently=False)
            logger.info('Sent appointment QR to email %s (booking id %s)', self.mail, self.pk)
        except Exception as e:
            logger.exception('Failed to send appointment email: %s', e)
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

