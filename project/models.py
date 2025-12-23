from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
class bookings(models.Model):
    Name = models.CharField(max_length=50)
    mail = models.EmailField()
    mobile = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?[0-9]{7,15}$', message='Enter a valid phone number')]
    )
    appointment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']

    def __str__(self):
        return self.Name

