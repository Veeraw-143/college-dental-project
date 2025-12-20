from django.db import models

# Create your models here.
class bookings(models.Model):
    Name = models.CharField(max_length=20)
    mail = models.EmailField()
    mobile = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

