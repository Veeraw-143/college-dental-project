from django.contrib import admin
from project.models import bookings
@admin.register(bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('Name', 'mail', 'mobile', 'appointment_date', 'created_at')
    search_fields = ('Name', 'mail', 'mobile')
    list_filter = ('appointment_date', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('Name', 'mail', 'mobile', 'appointment_date')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

# Customize the admin site header for a more seamless experience
admin.site.site_header = "SmileCare Admin"
admin.site.site_title = "SmileCare Admin Portal"
admin.site.index_title = "Site Administration"