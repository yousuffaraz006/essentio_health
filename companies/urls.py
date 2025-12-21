from django.urls import path
from .views import *

app_name = 'companies'

urlpatterns = [
    path('', companies_list_view, name='companies_list_url'),
    path('create/', company_create_view, name='company_create_url'),
    path('<int:pk>/', company_profile_view, name='company_profile_url'),
    path('<int:pk>/edit/', company_edit_view, name='company_edit_url'),
    path('<int:pk>/delete/', company_delete_view, name='company_delete_url'),

    # API-like endpoints for datatables
    path('<int:pk>/employees-json/', company_employees_json, name='company_employees_json_url'),
]