from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name='dashboard_url'),
    path('admin-users/', admin_users, name='admin_users_url'),
    path('companies/', companies, name='companies_url'),
]
