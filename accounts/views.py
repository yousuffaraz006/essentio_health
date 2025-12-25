from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated  # adjust as needed
from rest_framework.response import Response
from django.core.paginator import Paginator
from rest_framework.views import APIView
from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import render, get_object_or_404, redirect
from .serializers import ClientsCSVSerializer
from django.http import JsonResponse
from django.db import transaction
from .models import *
from .forms import *
import json

# Create your views here.

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def admin_users_list_view(request):
    members = (
        User.objects
        .select_related('member_profile')
        .prefetch_related('member_profile__roles')
        .filter(member_profile__roles__isnull=False)
        .distinct()
    )
    roles = Role.objects.all().order_by('name')
    return render(request, 'accounts/admin_users.html', {'members': members, 'roles': roles})

@require_POST
def admin_user_create_view(request):
    try:
        print("POST data received:", request.POST)
        data = request.POST

        first_name = data.get('firstname', '').strip()
        last_name = data.get('lastname', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        role_codes = data.getlist('roles')

        # ---- validations ----
        if not first_name or not email:
            print("First name or email missing")
            return JsonResponse({'error': 'First name and email are required'}, status=400)

        if User.objects.filter(email=email).exists():
            print("Email already registered:", email)
            return JsonResponse({'error': 'Email already registered'}, status=400)
        
        if not role_codes:
            print("No roles provided")
            return JsonResponse({'error': 'At least one role is required'}, status=400)

        if User.objects.filter(email=email).exists():
            print("User with this email already exists:", email)
            return JsonResponse({'error': 'User with this email already exists'}, status=400)

        # ---- username logic ----
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # ---- create user ----
        is_active_str = request.POST.get('is_active', 'True')
        is_active = is_active_str == 'True'
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active
        )

        profile = MemberProfile.objects.create(user=user)
        profile.phone = phone

        roles = Role.objects.filter(code__in=role_codes)
        profile.roles.set(roles)
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)

def admin_user_detail_view(request, user_id):
    user = User.objects.select_related('member_profile').prefetch_related('member_profile__roles').get(id=user_id)
    data = {
        'id': user.id,
        'firstname': user.first_name,
        'lastname': user.last_name,
        'email': user.email,
        'phone': user.member_profile.phone,
        'is_active': user.is_active,
        'roles': list(user.member_profile.roles.values_list('code', flat=True)),
    }
    return JsonResponse(data)

@require_POST
def admin_user_edit_view(request, pk):
    try:
        print("POST data received for edit:", request.POST)
        user = User.objects.select_related('member_profile').get(id=pk)

        data = request.POST
        role_codes = data.getlist('roles')
        is_active_str = request.POST.get('is_active', 'True')

        if not role_codes:
            return JsonResponse({'error': 'At least one role is required'}, status=400)
        
        # Check for email uniqueness (excluding the current user)
        new_email = data.get('email', '').strip()
        if User.objects.filter(email=new_email).exclude(id=pk).exists():
            return JsonResponse({'error': 'Email is already in use by another user.'}, status=400)

        user.first_name = data.get('firstname', '').strip()
        user.last_name = data.get('lastname', '').strip()
        user.email = data.get('email', '').strip()
        user.is_active = is_active_str == 'True'
        user.save()

        user.member_profile.phone = data.get('phone', '').strip()
        roles = Role.objects.filter(code__in=role_codes)
        user.member_profile.roles.set(roles)
        user.member_profile.save()
        return JsonResponse({'success': True, 'id': user.id})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)

def clients_list_view(request):
    return render(request, 'accounts/users_page.html')

def clients_list_api(request):
    qs = User.objects.filter(client_profile__isnull=False).select_related("client_profile").order_by('-date_joined')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(client_profile__phone__icontains=q) |
            Q(client_profile__city__icontains=q) |
            Q(client_profile__state__icontains=q) |
            Q(client_profile__country__icontains=q) |
            Q(client_profile__plan__icontains=q) |
            Q(client_profile__company__name__icontains=q)
        )

    # ---------------- DATE FILTERS (JOINED) ----------------
    joined_after = request.GET.get('joined_after')
    if joined_after:
        qs = qs.filter(date_joined__date__gte=joined_after)

    joined_before = request.GET.get('joined_before')
    if joined_before:
        qs = qs.filter(date_joined__date__lte=joined_before)

    # ---------------- PAGINATION ----------------
    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, 10)  # 10 users per page
    page_obj = paginator.get_page(page_number)

    # ---- BUILD RESPONSE ----
    results = []
    for u in page_obj:
        cp = u.client_profile  # Guaranteed to exist now

        results.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}".strip() or u.username,
            "email": u.email,

            "phone": cp.phone or "",
            "city": cp.city or "",
            "state": cp.state or "",
            "country": cp.country or "",
            "company": cp.company.name if cp.company else "",
            "plan": cp.plan or "",

            "joined": u.date_joined.strftime("%Y-%m-%d"),
            "is_active": u.is_active,
        })

    return JsonResponse({
        "results": results,
        "pagination": {
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }
    })

def add_clients_page(request):
    companies = Company.objects.all().order_by('name')
    selected_company = request.GET.get("company_id")  # catch passed company ID
    if request.method == 'GET':
        return render(
            request,
            'accounts/add_users_page.html',
            {'companies': companies, 'selected_company': selected_company}
        )

    # -------- POST: create client user --------
    data = request.POST

    firstname = data.get('firstname', '').strip()
    lastname = data.get('lastname', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    plan = data.get('plan')
    company_id = data.get('company')
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    country = data.get('country', '').strip()
    is_active = data.get('is_active') == 'on'

    # ---- validations ----
    if not firstname or not email or not plan:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'User with this email already exists'}, status=400)

    with transaction.atomic():
        # username generation
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # create user
        user = User.objects.create(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email,
            is_active=is_active,
        )

        # optional company
        company = None
        if company_id:
            company = Company.objects.filter(id=company_id).first()

        # create client profile
        ClientProfile.objects.create(
            user=user,
            company=company,
            plan=plan,
            phone=phone,
            city=city,
            state=state,
            country=country,
        )
    return redirect('accounts:clients_list_url')

def user_profile_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = getattr(user, 'client_profile',None)
    companies = Company.objects.all().order_by('name')
    return render(request, 'accounts/user_profile.html', {'user': user, 'profile': profile, 'companies': companies})

@require_POST
def update_clients_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    data = json.loads(request.body)
    section = data.get('section')
    field = data.get('field')
    value = data.get('value')

    # ---- allowed fields ----
    USER_FIELDS = {'first_name', 'last_name', 'email', 'is_active'}
    CLIENT_FIELDS = {'phone', 'city', 'state', 'country', 'plan', 'company'}

    if section == 'user':
        if field not in USER_FIELDS:
            return JsonResponse({'success': False}, status=400)

        # type handling
        if field == 'is_active':
            value = value is True or value == 'true'

        setattr(user, field, value)
        user.save(update_fields=[field])

    elif section == 'client_profile':
        profile = get_object_or_404(ClientProfile, user=user)

        if field not in CLIENT_FIELDS:
            return JsonResponse({'success': False}, status=400)

        # company is FK
        if field == 'company':
            try:
                value = int(value)
                value = Company.objects.filter(id=value).first()
            except (TypeError, ValueError):
                value = None

        setattr(profile, field, value)
        profile.save(update_fields=[field])

    else:
        return JsonResponse({'success': False}, status=400)

    return JsonResponse({'success': True})

def upload_bulk_clients_view(request):
    return render(request, 'accounts/add_bulk_users_page.html')

class ClientsCSVUploadView(APIView):

    def post(self, request):
        rows = request.data.get('rows', [])
        forced_company_id = request.GET.get('company_id')  # <── Check URL
        forced_company = None

        if forced_company_id:
            from companies.models import Company
            forced_company = Company.objects.filter(id=forced_company_id).first()

        # detect duplicate emails inside CSV upload
        emails = [r.get("email","").lower().strip() for r in rows]
        duplicate_emails = {e for e in emails if emails.count(e) > 1 and e != ""}

        rowErrors = []
        success = True

        for row in rows:
            if forced_company:
                row["company"] = ""      # remove CSV company to avoid confusion

            s = ClientsCSVSerializer(
                data=row,
                context={
                    "request": request,
                    "duplicate_emails": duplicate_emails,
                    "force_company": forced_company          # <── add here
                }
            )

            if not s.is_valid():
                errors = {k: ", ".join(v) for k,v in s.errors.items()}
                errors["_rowErrorCount"] = len(s.errors)
                rowErrors.append(errors)
                success = False
            else:
                rowErrors.append({})

        if not success:
            return Response({"success": False, "rowErrors": rowErrors}, status=400)

        # create after validated
        created_ids = []
        for row in rows:
            s = ClientsCSVSerializer(
                data=row,
                context={
                    "request": request,
                    "force_company": forced_company          # <── must include
                }
            )
            s.is_valid(raise_exception=True)
            obj = s.save()
            created_ids.append(obj.id)
        
        return Response({"success": True, "created_ids": created_ids})
