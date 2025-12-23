from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .forms import CompanyForm
from .models import Company
from accounts.models import *
from django.views.decorators.http import require_POST

def companies_list_view(request):
    companies = Company.objects.all()
    data = []
    for company in companies:
        data.append({
            'id': company.id,
            'name': company.name,
            'city': company.city,
            'state': company.state,
            'active_employees_count': ClientProfile.objects.filter(company=company, user__is_active=True).count(),
        })
    return render(request, 'companies/companies_list.html', {'companies': data})

@require_POST
def company_create_view(request):
    form = CompanyForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Company created successfully.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def company_edit_view(request, pk):
    c = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST, instance=c)
    if form.is_valid():
        c = form.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def company_delete_view(request, pk):
    c = get_object_or_404(Company, pk=pk)
    c.delete()
    return JsonResponse({'success': True})

def company_profile_view(request, pk):
    company = get_object_or_404(Company, pk=pk)
    users = User.objects.filter(client_profile__company=company).select_related('client_profile')
    return render(request, 'companies/company_profile.html', {'company': company, 'users': users})

def company_employees_json(request, pk):
    company = get_object_or_404(Company, pk=pk)
    qs = ClientProfile.objects.filter(company=company).select_related('user')
    data = []
    for p in qs:
        data.append({
            'id': p.user.id,
            'first_name': p.user.first_name,
            'last_name': p.user.last_name,
            'email': p.user.email,
            'phone': p.phone,
            'city': p.city,
            'state': p.state,
            'country': p.country,
        })
    return JsonResponse({'data': data})
