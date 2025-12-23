from django.contrib import admin, messages
from django.urls import reverse
import logging
from project.models import bookings

logger = logging.getLogger(__name__)

@admin.register(bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('Name', 'mail', 'mobile', 'appointment_date', 'status', 'created_at')
    search_fields = ('Name', 'mail', 'mobile')
    list_filter = ('appointment_date', 'status', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    actions = ['accept_bookings']
    fieldsets = (
        (None, {'fields': ('Name', 'mail', 'mobile', 'appointment_date', 'status')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def save_model(self, request, obj, form, change):
        # if status changed to accepted, send QR and notifications
        if change and hasattr(obj, 'pk'):
            try:
                prev = bookings.objects.get(pk=obj.pk)
            except bookings.DoesNotExist:
                prev = None
            if prev and prev.status != obj.status and obj.status == bookings.STATUS_ACCEPTED:
                super().save_model(request, obj, form, change)
                try:
                    obj.send_qr_and_notify(request=request, sms_enabled=False)
                    messages.success(request, f'Booking {obj.pk} accepted and QR sent to user')
                except Exception as e:
                    messages.error(request, f'Booking accepted but sending QR failed: {e}')
                return
        super().save_model(request, obj, form, change)

    def accept_bookings(self, request, queryset):
        count = 0
        for b in queryset:
            if b.status != bookings.STATUS_ACCEPTED:
                b.status = bookings.STATUS_ACCEPTED
                b.save()
                try:
                    b.send_qr_and_notify(request=request, sms_enabled=False)
                    count += 1
                except Exception as e:
                    logger.exception('Failed to send QR for booking %s: %s', b.pk, e)
        self.message_user(request, f'Accepted and notified {count} booking(s)', level=messages.SUCCESS)
    accept_bookings.short_description = 'Accept selected bookings and notify users'

# Customize the admin site header for a more seamless experience
admin.site.site_header = "SmileCare Admin"
admin.site.site_title = "SmileCare Admin Portal"
admin.site.index_title = "Site Administration"