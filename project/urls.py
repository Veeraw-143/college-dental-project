"""
URL configuration for project app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services_view, name='services'),
    path('doctors/', views.doctors_view, name='doctors'),
    path('contact/', views.contact_view, name='contact'),
    path('booking/', views.booking, name='booking'),
    path('booking/<int:pk>/qr/', views.booking_qr, name='booking_qr'),
    path('api/booked-slots/', views.get_booked_slots, name='get_booked_slots'),
    path('api/doctors-services/', views.get_doctors_and_services, name='get_doctors_and_services'),
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    path('manage-appointments/', views.manage_appointments, name='manage_appointments'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/admin-stats/', views.admin_stats_api, name='admin_stats_api'),
    path('admin-panel/logout/', views.logout_view, name='admin_logout'),
    
    # Feedback URLs
    path('api/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('api/get-feedback/', views.get_all_feedback, name='get_all_feedback'),
]
