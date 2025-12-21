from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def admin_users(request):
    return render(request, 'accounts/admin_users.html')

def companies(request):
    return render(request, 'accounts/companies.html')

def manage_company(request):
    if request.method == 'GET':
        return JsonResponse({'success': True})
    if request.method == 'POST':
        # Process form data here
        pass
        return JsonResponse({'success': True})

    return JsonResponse({'status': 'success'})