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
]
