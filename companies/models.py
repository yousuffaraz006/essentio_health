from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    ceo = models.CharField(max_length=255, blank=True)
    size = models.CharField(max_length=120, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='companies_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='companies_updated'
    )

    def __str__(self):
        return self.name

class CompanyPOC(models.Model):
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='pocs'
    )

    designation = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    access_master_dashboard = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"