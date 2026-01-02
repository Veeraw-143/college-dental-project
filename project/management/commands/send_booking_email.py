from django.core.management.base import BaseCommand, CommandError
from project.models import bookings

class Command(BaseCommand):
    help = 'Send booking email (accept or reject) for a given booking id (useful to test SMTP and delivery)'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, required=True, help='Booking ID to send email for')
        parser.add_argument('--type', choices=['accept', 'reject'], default='accept', help='Which email to send')

    def handle(self, *args, **options):
        bid = options['id']
        typ = options['type']
        try:
            b = bookings.objects.get(pk=bid)
        except bookings.DoesNotExist:
            raise CommandError(f'Booking with id {bid} does not exist')

        try:
            if typ == 'accept':
                b.send_qr_and_notify(request=None, sms_enabled=False)
                self.stdout.write(self.style.SUCCESS(f'Acceptance email sent (or printed) for booking {bid} to {b.mail}'))
            else:
                b.send_rejection_notification(request=None)
                self.stdout.write(self.style.SUCCESS(f'Rejection email sent (or printed) for booking {bid} to {b.mail}'))
        except Exception as e:
            raise CommandError(f'Failed to send email for booking {bid}: {e}')