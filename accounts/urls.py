from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    # path('admin-users/', admin_users, name='admin_users_url'),
    # path('users/', manage_users, name='manage_users_url'),
    # path('companies/', companies, name='companies_url'),
    path('', dashboard, name='dashboard_url'),
    path('admin-users/', admin_users_list_view, name='admin_users_list_url'),
    path('admin-users/create/', admin_user_create_view, name='admin_user_create_url'),
    path('admin-users/<int:pk>/edit/', admin_user_edit_view, name='admin_user_edit_url'),
    path('admin-users/<int:pk>/delete/', admin_user_delete_view, name='admin_user_delete_url'),
    path('user/<int:pk>/', user_profile_view, name='user_profile_url'),
]
