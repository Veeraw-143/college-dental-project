"""
URL configuration for project app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('booking/<int:pk>/qr/', views.booking_qr, name='booking_qr'),
    path('api/booked-slots/', views.get_booked_slots, name='get_booked_slots'),
    path('api/doctors-services/', views.get_doctors_and_services, name='get_doctors_and_services'),
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    path('manage-appointments/', views.manage_appointments, name='manage_appointments'),
]
