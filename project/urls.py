"""
URL configuration for project app.
"""
from django.urls import path
from . import views, async_views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services_view, name='services'),
    path('doctors/', views.doctors_view, name='doctors'),
    path('contact/', views.contact_view, name='contact'),
    path('feedback/', views.feedback_view, name='feedback'),
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
    
    # Chatbot URLs
    path('api/chatbot-message/', views.chatbot_message_api, name='chatbot_message'),
    path('api/faq/', views.get_faq_list, name='get_faq_list'),
    
    # Feedback URLs
    path('api/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('api/get-feedback/', views.get_all_feedback, name='get_all_feedback'),
    
    # Real-time & Async Updates URLs
    path('api/bookings/updates/', async_views.get_booking_updates, name='booking_updates'),
    path('api/otp/status/', async_views.get_otp_status, name='otp_status'),
    path('api/dashboard/stats/', async_views.get_dashboard_stats, name='dashboard_stats'),
    path('api/booking/<int:booking_id>/details/', async_views.get_booking_detail, name='booking_detail'),
    path('api/otp/<str:email>/status/', async_views.get_otp_verification_status, name='otp_verification_status'),
    path('api/subscribe/updates/', async_views.subscribe_to_updates, name='subscribe_updates'),
]
