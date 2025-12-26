from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('', dashboard, name='dashboard_url'),
    path('admin-users/', admin_users_list_view, name='admin_users_list_url'),
    path('admin-users/create/', admin_user_create_view, name='admin_user_create_url'),
    path('admin-users/<int:user_id>/detail/', admin_user_detail_view, name='admin_user_detail_url'),
    path('admin-users/<int:pk>/edit/', admin_user_edit_view, name='admin_user_edit_url'),
    path('users/', clients_list_view, name='clients_list_url'),
    path('users/api/', clients_list_api, name='users_list_api_url'),
    path('users/add/', add_clients_page, name='add_user_url'),
    path('users/<int:pk>/', user_profile_view, name='user_profile_url'),
    path('users/update/<int:user_id>/', update_clients_view, name='update_clients_url'),
    path('users/upload-bulk/', ClientsBulkUploadView.as_view(), name='upload_bulk_clients_page_url'),
    path('users/upload-bulk/validate/', ClientsBulkUploadValidateView.as_view(), name='upload_bulk_clients_validate_url'),
]
