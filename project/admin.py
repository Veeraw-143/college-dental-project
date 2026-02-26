from django.contrib import admin, messages
from django.urls import reverse
import logging
from project.models import bookings, Doctor, Service, OTPVerification, Feedback
from django.utils.html import format_html
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============= DOCTOR ADMIN =============
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'availability_display', 'experience_display', 'email', 'is_active_display', 'created_at')
    search_fields = ('name', 'specialization', 'email')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'photo_preview')
    
    # Single fieldset - all information on one page for easy data entry
    fieldsets = (
        (None, {
            'fields': ('name', 'specialization', 'email', 'phone', 'experience_years', 'bio', 'photo', 'photo_preview', 'availability_days', 'is_active', 'created_at')
        }),
    )
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 50%;" />', obj.photo.url)
        return 'No photo'
    photo_preview.short_description = 'Photo Preview'

    def experience_display(self, obj):
        return f"{obj.experience_years} years"
    experience_display.short_description = 'Experience'

    def availability_display(self, obj):
        days = obj.get_available_days()
        if len(days) == 7:
            return '✓ All Days'
        days_str = ', '.join(days)
        return f"📅 {days_str}"
    availability_display.short_description = 'Available Days'

    def is_active_display(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    is_active_display.short_description = 'Status'


# ============= SERVICE ADMIN =============
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_display', 'cost_display', 'is_active_display', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)
    
    # Single fieldset - all information on one page
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'duration_minutes', 'cost', 'is_active', 'created_at')
        }),
    )

    def duration_display(self, obj):
        return f"{obj.duration_minutes} min"
    duration_display.short_description = 'Duration'

    def cost_display(self, obj):
        return f"₹{obj.cost}"
    cost_display.short_description = 'Cost'

    def is_active_display(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓' if obj.is_active else '✗'
        return format_html('<span style="color: {}; font-weight: bold; font-size: 18px;">{}</span>', color, status)
    is_active_display.short_description = 'Status'


# ============= OTP VERIFICATION ADMIN =============
@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_verified_display', 'attempts_display', 'is_valid_display', 'created_at')
    search_fields = ('email',)
    list_filter = ('is_verified', 'created_at')
    readonly_fields = ('created_at', 'expires_at')
    
    # Single fieldset - all information on one page
    fieldsets = (
        (None, {
            'fields': ('email', 'otp_code', 'is_verified', 'attempts', 'created_at', 'expires_at')
        }),
    )
    can_delete = True

    def is_verified_display(self, obj):
        color = 'green' if obj.is_verified else 'red'
        status = '✓ Verified' if obj.is_verified else '✗ Not Verified'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    is_verified_display.short_description = 'Status'

    def attempts_display(self, obj):
        return f"{obj.attempts}/5"
    attempts_display.short_description = 'Attempts'

    def is_valid_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">EXPIRED</span>')
        color = 'green' if obj.is_valid() else 'orange'
        status = 'VALID' if obj.is_valid() else 'INVALID'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    is_valid_display.short_description = 'Validity'


# ============= BOOKINGS ADMIN (ENHANCED) =============
@admin.register(bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id',
        'Name',
        'mobile_display',
        'appointment_info',
        'doctor_display',
        'service_display',
        'status_badge',
        'otp_status',
        'created_at'
    )
    search_fields = ('Name', 'mail', 'mobile')
    list_filter = ('appointment_date', 'time', 'status', 'created_at', 'preferred_doctor', 'preferred_service')
    readonly_fields = ('created_at', 'time_display', 'appointment_summary')
    ordering = ('-created_at',)
    actions = ['accept_bookings', 'reject_bookings', 'mark_completed', 'send_reminder_email']

    # Single fieldset - all information on one page for easy data entry
    fieldsets = (
        (None, {
            'fields': ('Name', 'mail', 'mobile', 'appointment_date', 'time', 'preferred_doctor', 'preferred_service', 'status', 'otp_verified', 'reminder_sent', 'appointment_summary', 'created_at')
        }),
    )

    def booking_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.pk)
    booking_id.short_description = 'Booking ID'

    def mobile_display(self, obj):
        return obj.mobile
    mobile_display.short_description = 'Mobile'

    def time_display(self, obj):
        """Display time in 12-hour format."""
        return obj.get_time_12hr() if obj.time else '-'
    time_display.short_description = 'Time'

    def appointment_info(self, obj):
        return format_html(
            '{}<br/><small style="color: #666;">{}</small>',
            obj.appointment_date or '-',
            obj.get_time_12hr() if obj.time else '-'
        )
    appointment_info.short_description = 'Appointment'

    def doctor_display(self, obj):
        if obj.preferred_doctor:
            return format_html(
                '<strong>{}</strong><br/><small style="color: #666;">{}</small>',
                obj.preferred_doctor.name,
                obj.preferred_doctor.specialization
            )
        return '-'
    doctor_display.short_description = 'Doctor'

    def service_display(self, obj):
        if obj.preferred_service:
            return obj.preferred_service.name
        return '-'
    service_display.short_description = 'Service'

    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'accepted': '#4caf50',
            'rejected': '#f44336',
            'completed': '#2196f3',
            'cancelled': '#9c27b0'
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def otp_status(self, obj):
        color = 'green' if obj.otp_verified else 'orange'
        status = '✓' if obj.otp_verified else '✗'
        return format_html('<span style="color: {}; font-weight: bold; font-size: 18px;">{}</span>', color, status)
    otp_status.short_description = 'OTP'

    def appointment_summary(self, obj):
        """Display a summary of the appointment"""
        summary = f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
            <strong>Booking ID:</strong> #{obj.pk}<br/>
            <strong>Patient:</strong> {obj.Name}<br/>
            <strong>Email:</strong> {obj.mail}<br/>
            <strong>Phone:</strong> {obj.mobile}<br/>
            <strong>Date & Time:</strong> {obj.appointment_date} at {obj.get_time_12hr()}<br/>
            <strong>Doctor:</strong> {obj.preferred_doctor or 'Not specified'}<br/>
            <strong>Service:</strong> {obj.preferred_service or 'Not specified'}<br/>
            <strong>Status:</strong> {obj.get_status_display()}<br/>
            <strong>OTP Verified:</strong> {'Yes' if obj.otp_verified else 'No'}<br/>
            <strong>Reminder Sent:</strong> {'Yes' if obj.reminder_sent else 'No'}<br/>
            <strong>Booked on:</strong> {obj.created_at.strftime('%Y-%m-%d %H:%M')}
        </div>
        """
        return format_html(summary)
    appointment_summary.short_description = 'Appointment Summary'

    def save_model(self, request, obj, form, change):
        """Handle status changes and send notifications"""
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
                        messages.success(request, f'✓ Booking #{obj.pk} accepted and QR sent to user')
                    except Exception as e:
                        messages.error(request, f'✗ Booking accepted but sending QR failed: {e}')
                    return
                # Rejected
                elif obj.status == bookings.STATUS_REJECTED:
                    super().save_model(request, obj, form, change)
                    try:
                        obj.send_rejection_notification(request=request)
                        messages.success(request, f'✓ Booking #{obj.pk} rejected and user notified')
                    except Exception as e:
                        messages.error(request, f'✗ Booking rejected but notification failed: {e}')
                    return
        
        super().save_model(request, obj, form, change)

    def accept_bookings(self, request, queryset):
        """Admin action to accept multiple bookings"""
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
            self.message_user(request, f'✓ Accepted and notified {sent} booking(s)', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'✗ Failed for {len(failed)} booking(s): {failed}', level=messages.ERROR)
    accept_bookings.short_description = '✓ Accept and notify'

    def reject_bookings(self, request, queryset):
        """Admin action to reject bookings"""
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
            self.message_user(request, f'✓ Rejected and notified {sent} booking(s)', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'✗ Failed for {len(failed)} booking(s): {failed}', level=messages.ERROR)
    reject_bookings.short_description = '✗ Reject and notify'

    def mark_completed(self, request, queryset):
        """Mark appointments as completed"""
        updated = queryset.update(status=bookings.STATUS_COMPLETED)
        self.message_user(request, f'✓ Marked {updated} appointment(s) as completed', level=messages.SUCCESS)
    mark_completed.short_description = '✓ Mark as completed'

    def send_reminder_email(self, request, queryset):
        """Send reminder emails for selected bookings"""
        sent = 0
        failed = []
        for b in queryset:
            try:
                b.send_reminder_notification(request=request)
                b.reminder_sent = True
                b.save()
                sent += 1
            except Exception as e:
                logger.exception('Failed to send reminder for booking %s: %s', b.pk, e)
                failed.append(b.pk)
        
        if sent:
            self.message_user(request, f'✓ Sent reminder to {sent} patient(s)', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'✗ Failed to send reminder to {len(failed)} patient(s)', level=messages.ERROR)
    send_reminder_email.short_description = '✉ Send reminder email'


# ============= FEEDBACK ADMIN =============
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'message_preview', 'is_active_display', 'created_at')
    search_fields = ('name', 'message')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)
    
    # Single fieldset - all information on one page
    fieldsets = (
        (None, {
            'fields': ('name', 'message', 'is_active', 'created_at')
        }),
    )

    def message_preview(self, obj):
        preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return preview
    message_preview.short_description = 'Message'

    def is_active_display(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    is_active_display.short_description = 'Status'


# Customize the admin site
admin.site.site_header = "Surabi Dental Care"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Dashboard"
