from django.contrib.auth.models import User
from companies.models import *
from django.db import models



class Role(models.Model):
    code = models.CharField(max_length=32, blank=True, unique=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    phone = models.CharField(max_length=30, blank=True)
    roles = models.ManyToManyField(Role, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='members_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='members_updated'
    )

    def is_admin_user(self):
        return self.roles.exists()

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employees'
    )
    PLAN_CHOICES = (
        ('ELITE', 'Elite'),
        ('CORE', 'Core'),
        ('DIGITAL', 'Digital'),
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_updated'
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username