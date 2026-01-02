from django.contrib import admin, messages
from django.urls import reverse
import logging
from project.models import bookings

logger = logging.getLogger(__name__)

@admin.register(bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('Name', 'mail', 'mobile', 'appointment_date', 'time_display', 'status', 'created_at')
    search_fields = ('Name', 'mail', 'mobile')
    list_filter = ('appointment_date', 'time', 'status', 'created_at')
    readonly_fields = ('created_at', 'time_display')
    ordering = ('-created_at',)
    actions = ['accept_bookings', 'reject_bookings']
    fieldsets = (
        (None, {'fields': ('Name', 'mail', 'mobile', 'appointment_date', 'time', 'status')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def time_display(self, obj):
        """Display time in 12-hour format."""
        return obj.get_time_12hr()
    time_display.short_description = 'Time (12-hour)'

    def save_model(self, request, obj, form, change):
        # if status changed to accepted or rejected, send appropriate notifications
        if change and hasattr(obj, 'pk'):
            try:
                prev = bookings.objects.get(pk=obj.pk)
            except bookings.DoesNotExist:
                prev = None
            if prev and prev.status != obj.status:
                # Accepted
                if obj.status == bookings.STATUS_ACCEPTED:
                    super().save_model(request, obj, form, change)
                    try:
                        obj.send_qr_and_notify(request=request, sms_enabled=False)
                        messages.success(request, f'Booking {obj.pk} accepted and QR sent to user')
                    except Exception as e:
                        messages.error(request, f'Booking accepted but sending QR failed: {e}')
                    return
                # Rejected
                if obj.status == bookings.STATUS_REJECTED:
                    super().save_model(request, obj, form, change)
                    try:
                        obj.send_rejection_notification(request=request)
                        messages.success(request, f'Booking {obj.pk} rejected and user notified')
                    except Exception as e:
                        messages.error(request, f'Booking rejected but sending notification failed: {e}')
                    return
        super().save_model(request, obj, form, change)

    def accept_bookings(self, request, queryset):
        sent = 0
        failed = []
        for b in queryset:
            if b.status != bookings.STATUS_ACCEPTED:
                b.status = bookings.STATUS_ACCEPTED
                try:
                    b.save()
                    try:
                        b.send_qr_and_notify(request=request, sms_enabled=False)
                        sent += 1
                    except Exception as e:
                        logger.exception('Failed to send QR for booking %s: %s', b.pk, e)
                        failed.append(b.pk)
                except Exception as e:
                    logger.exception('Failed to save accepted status for booking %s: %s', b.pk, e)
                    failed.append(b.pk)
        if sent:
            self.message_user(request, f'Accepted and notified {sent} booking(s)', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'Failed to accept or notify {len(failed)} booking(s): {failed}', level=messages.ERROR)
    accept_bookings.short_description = 'Accept selected bookings and notify users'

    def reject_bookings(self, request, queryset):
        """Admin action to reject selected bookings and send rejection emails."""
        sent = 0
        failed = []
        for b in queryset:
            if b.status != bookings.STATUS_REJECTED:
                b.status = bookings.STATUS_REJECTED
                try:
                    b.save()
                    try:
                        b.send_rejection_notification(request=request)
                        sent += 1
                    except Exception as e:
                        logger.exception('Failed to send rejection email for booking %s: %s', b.pk, e)
                        failed.append(b.pk)
                except Exception as e:
                    logger.exception('Failed to save rejected status for booking %s: %s', b.pk, e)
                    failed.append(b.pk)
        if sent:
            self.message_user(request, f'Rejected and notified {sent} booking(s)', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'Failed to reject or notify {len(failed)} booking(s): {failed}', level=messages.ERROR)
    reject_bookings.short_description = 'Reject selected bookings and notify users'

# Customize the admin site header for a more seamless experience
admin.site.site_header = "Surabi Dental Care Admin"
admin.site.site_title = "Surabi Dental Care Admin Portal"
admin.site.index_title = "Site Administration"