from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    ceo = models.CharField(max_length=255, blank=True)
    size_of_business = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name