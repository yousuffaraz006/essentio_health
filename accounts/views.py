from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, IntegerField
from django.shortcuts import render, get_object_or_404, redirect
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
    users = (
        User.objects
        .select_related('client_profile', 'client_profile__company')
        .filter(client_profile__isnull=False)
        .exclude(is_superuser=True)
        .annotate(
            has_company=Case(
                When(client_profile__company__isnull=False, then=Value(0)),
                When(client_profile__company__isnull=True, then=Value(1)),
                output_field=IntegerField(),
            )
        )
        .order_by('has_company')
    )
    return render(request, 'accounts/users_page.html', {'users': users})

def add_clients_page(request):
    if request.method == 'GET':
        companies = Company.objects.all().order_by('name')
        return render(
            request,
            'accounts/add_users_page.html',
            {'companies': companies}
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