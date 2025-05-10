from django.db import models
from django.utils import timezone

class LoginAttempt(models.Model):
    email = models.EmailField()
    date = models.DateField(default=timezone.now)
    fails = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('email', 'date')
        ordering = ['-date']
