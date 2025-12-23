# college-dental-project

## Notifications (QR + SMS)

This project includes an admin workflow enhancement: when a booking's **status** is set to **Accepted** in the Django admin (or the `accept_bookings` admin action is used), the system will generate a QR code for the appointment and send it to the user's **email**. Optionally, SMS notifications using Twilio can be enabled.

Requirements:
- Python packages: `qrcode[pil]` and `Pillow` (for generating QR PNGs).
- (Optional) `twilio` if you want to send SMS notifications.

Install:

```bash
pip install qrcode[pil] Pillow twilio
```

Configuration (recommended in environment variables):
- `SITE_URL` — public base URL for building QR endpoints (default: `http://127.0.0.1:8000`)
- `EMAIL_BACKEND` and `DEFAULT_FROM_EMAIL` — configure nomal email delivery; by default dev uses the console backend
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` — (optional) to enable SMS sending

Usage:
- Run migrations (a `status` field was added to bookings):

```bash
python manage.py makemigrations
python manage.py migrate
```

- Accept a booking via the admin (set status to "Accepted") or use the **Accept selected bookings and notify users** action. Emails will be printed to console in development by default unless you configure an SMTP backend.

SMTP configuration (example):

```bash
# set these env vars before running the site
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.example.com
export EMAIL_PORT=587
export EMAIL_HOST_USER=your-smtp-user
export EMAIL_HOST_PASSWORD=your-smtp-password
export EMAIL_USE_TLS=true
export DEFAULT_FROM_EMAIL=no-reply@smilecare.example
```

When `EMAIL_BACKEND` is unset the project uses Django's console email backend which prints email contents to the server console rather than sending them. Set the SMTP env vars above to send real emails in staging/production.

Quick testing helpers:

- Run a local SMTP debug server (prints incoming SMTP traffic) and point Django at it for quick testing:

```bash
# run in a separate terminal (Python 3)
python -m smtpd -n -c DebuggingServer localhost:1025
# then set these env vars for testing
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=localhost
export EMAIL_PORT=1025
export EMAIL_USE_TLS=false
```

- Or use the provided management command to send an email for a specific booking (helpful after configuring SMTP):

```bash
python manage.py send_booking_email --id 123 --type accept
```

