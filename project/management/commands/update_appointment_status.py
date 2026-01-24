from django.core.management.base import BaseCommand
from project.views import update_expired_appointments
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update status of appointments that have passed their scheduled time'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting appointment status update job...'))
        
        try:
            updated_count = update_expired_appointments()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Updated {updated_count} expired appointment(s) to COMPLETED status'
                )
            )
            logger.info(f'Appointment status update job completed: {updated_count} updated')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error updating appointments: {str(e)}')
            )
            logger.error(f'Error in update_expired_appointments: {str(e)}', exc_info=True)
