from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import *
from django.contrib import messages
from django.http import JsonResponse
from .models import Company
from .forms import CompanyForm
import json

def companies_list_api(request):
    qs = Company.objects.all().order_by('name')

    # ---- global search ----
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(city__icontains=q) |
            Q(state__icontains=q) |
            Q(country__icontains=q)
        )

    # ---- date filters ----
    created_after = request.GET.get('created_after')
    if created_after:
        qs = qs.filter(created_at__date__gte=created_after)

    created_before = request.GET.get('created_before')
    if created_before:
        qs = qs.filter(created_at__date__lte=created_before)

    qs = qs.order_by('-created_at')

    # ---- pagination ----
    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    data = {
        'results': [
            {
                'id': company.id,
                'added_on': company.created_at.strftime('%Y-%m-%d'),
                'name': company.name,
                'city': company.city,
                'state': company.state,
                'active_users': ClientProfile.objects.filter(company=company, user__is_active=True).count(),
            }
            for company in page_obj
        ],
        'pagination': {
            'page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    }

    return JsonResponse(data)

def companies_list_view(request):
    return render(request, 'companies/companies_list.html')

@require_POST
def company_create_view(request):
    form = CompanyForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Company created successfully.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def company_edit_view(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    data = json.loads(request.body)

    field = data.get('field')
    value = data.get('value')

    allowed_fields = {
        'name', 'ceo', 'size', 'city', 'state', 'country', 'notes'
    }

    if field not in allowed_fields:
        return JsonResponse({'success': False}, status=400)

    setattr(company, field, value)
    company.save(update_fields=[field])

    return JsonResponse({'success': True})

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

# @require_GET
def company_poc_list_url(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    pocs = company.pocs.all().order_by('name')
    print( pocs )
    data = [
        {
            'id': poc.id,
            'name': poc.name,
            'designation': poc.designation,
            'email': poc.email,
            'access_master_dashboard': poc.access_master_dashboard,
        }
        for poc in pocs
    ]

    return JsonResponse({'pocs': data})

@require_POST
def company_poc_create_url(request):
    company_id = request.POST.get('company_id')
    name = request.POST.get('name')
    designation = request.POST.get('designation')
    email = request.POST.get('email')
    access_master_dashboard = request.POST.get('access_master_dashboard') == 'true'

    if not all([company_id, name, designation, email]):
        return JsonResponse(
            {'success': False, 'error': 'Missing required fields'},
            status=400
        )

    company = get_object_or_404(Company, id=company_id)

    poc = CompanyPOC.objects.create(
        company=company,
        name=name,
        designation=designation,
        email=email,
        access_master_dashboard=access_master_dashboard
    )

    return JsonResponse({
        'success': True,
        'poc': {
            'id': poc.id,
            'name': poc.name,
            'designation': poc.designation,
            'email': poc.email,
            'access_master_dashboard': poc.access_master_dashboard
        }
    })

@require_POST
def company_poc_update_url(request, poc_id):
    poc = get_object_or_404(CompanyPOC, id=poc_id)

    poc.name = request.POST.get('name')
    poc.designation = request.POST.get('designation')
    poc.email = request.POST.get('email')
    poc.access_master_dashboard = request.POST.get('access_master_dashboard') == 'true'

    if not all([poc.name, poc.designation, poc.email]):
        return JsonResponse(
            {'success': False, 'error': 'Missing required fields'},
            status=400
        )

    poc.save()

    return JsonResponse({'success': True})

@require_POST
def company_poc_delete_url(request, poc_id):
    poc = get_object_or_404(CompanyPOC, id=poc_id)
    poc.delete()
    return JsonResponse({'success': True})