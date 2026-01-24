from django.core.management.base import BaseCommand
from project.views import send_reminder_emails
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminder emails for appointments scheduled for tomorrow'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting reminder email job...'))
        
        try:
            result = send_reminder_emails()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Reminder emails sent successfully!\n'
                    f'  - Sent to {result["sent"]} patients\n'
                    f'  - Failed: {result["failed"]}'
                )
            )
            logger.info(f'Reminder email job completed: {result}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending reminder emails: {str(e)}')
            )
            logger.error(f'Error in send_reminder_emails: {str(e)}', exc_info=True)
