from django.urls import path
from .views import *

app_name = 'companies'

urlpatterns = [
    path('', companies_list_view, name='companies_page_url'),
    path('create/', company_create_view, name='company_create_url'),
    path('<int:pk>/', company_profile_view, name='company_profile_url'),
    path('<int:company_id>/edit/', company_edit_view, name='company_edit_url'),
    path('<int:pk>/delete/', company_delete_view, name='company_delete_url'),

    # API-like endpoints for datatables
    path('api/', companies_list_api, name='companies_list_url'),
    path('<int:pk>/employees-json/', company_employees_json, name='company_employees_json_url'),

    path('pocs/<int:company_id>/', company_poc_list_url, name='company_poc_list_url'),
    path('pocs/create/', company_poc_create_url, name='company_poc_create_url'),
    path('pocs/<int:poc_id>/update/', company_poc_update_url, name='company_poc_update_url'),
    path('pocs/<int:poc_id>/delete/', company_poc_delete_url, name='company_poc_delete_url'),
]