from django.db import models
from django.contrib.auth.models import User
from companies.models import *



class Role(models.Model):
    code = models.CharField(max_length=32, blank=True, unique=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

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

    roles = models.ManyToManyField(Role, blank=True)
    def is_admin_user(self):
        return self.roles.exists()

    def __str__(self):
        return self.user.get_full_name() or self.user.username