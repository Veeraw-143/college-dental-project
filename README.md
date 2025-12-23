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

- Accept a booking via the admin (set status to "Accepted") or use the **Accept selected bookings and notify users** action. Emails will be printed to console in development unless an SMTP backend is configured.

