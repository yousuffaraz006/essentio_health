from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated  # adjust as needed
from rest_framework.response import Response
from django.core.paginator import Paginator
from rest_framework.views import APIView
from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from .serializers import ClientsCSVSerializer
from django.http import JsonResponse
from django.db import transaction
from .models import *
from .forms import *
import json, re

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
    member_users = User.objects.filter(member_profile__isnull=False).order_by('first_name')
    selected_company = request.GET.get("company_id")  # catch passed company ID
    if request.method == 'GET':
        return render(
            request,
            'accounts/add_users_page.html',
            {'companies': companies, 'selected_company': selected_company, 'member_users': member_users}
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

    health_coach_id = request.POST.get('health_coach')

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
            health_coach=User.objects.filter(id=health_coach_id).first() if health_coach_id else None
        )
    return redirect('accounts:clients_list_url')

def user_profile_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = getattr(user, 'client_profile',None)
    companies = Company.objects.all().order_by('name')
    member_users = User.objects.filter(member_profile__isnull=False).order_by('first_name')
    return render(request, 'accounts/user_profile.html', {'user': user, 'profile': profile, 'companies': companies, 'member_users': member_users})

@require_POST
def update_clients_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    data = json.loads(request.body)
    section = data.get('section')
    field = data.get('field')
    value = data.get('value')

    # ---- allowed fields ----
    USER_FIELDS = {'first_name', 'last_name', 'email', 'is_active'}
    CLIENT_FIELDS = {'phone', 'city', 'state', 'country', 'plan', 'company', 'health_coach'}

    if field == 'health_coach':
        try:
            value = int(value)
            value = User.objects.filter(id=value, member_profile__isnull=False).first()
        except:
            value = None

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

class ClientsBulkUploadValidateView(APIView):
    """
    POST: Accepts { rows: [...] } and returns per-row errors without creating.
    Response:
      - If any errors: HTTP 200 with { success: False, rowErrors: [...] }
      - If no errors: HTTP 200 with { success: True }
    """
    def post(self, request):
        rows = request.data.get('rows', []) if isinstance(request.data, dict) else []
        if not isinstance(rows, list):
            return Response({"success": False, "message": "Invalid payload: 'rows' must be a list."},
                            status=status.HTTP_400_BAD_REQUEST)

        row_errors, total_errors = validate_csv_rows(rows, request=request)
        if total_errors > 0:
            return Response({"success": False, "rowErrors": row_errors}, status=status.HTTP_200_OK)

        return Response({"success": True}, status=status.HTTP_200_OK)

def validate_csv_rows(rows, request=None):
    """
    Validate a list of row dicts coming from CSV.

    Input:
      rows: list of dicts, each dict has keys:
        first_name,last_name,email,phone,city,state,country,company,plan

    Output:
      (row_errors, total_errors)
      row_errors: list of dicts (same length as rows) where each dict maps field -> error string and includes "_rowErrorCount" key (int)
      total_errors: sum of all _rowErrorCount
    """
    # Prepare return structure
    row_errors = []
    total_errors = 0

    if not isinstance(rows, list):
        return [], 0

    # Normalize and collect CSV emails (for duplicate detection)
    csv_emails_lower = []
    for r in rows:
        e = (r.get('email') or '').strip().lower()
        csv_emails_lower.append(e)

    # Preload existing emails from DB (lowercase) for quick membership tests
    existing_emails_qs = User.objects.filter(email__isnull=False).values_list('email', flat=True)
    existing_emails = set([e.lower() for e in existing_emails_qs if e])

    # Preload companies for all company names present in CSV (lower -> Company)
    csv_company_names = set(
        (r.get('company') or '').strip().lower() for r in rows if (r.get('company') or '').strip()
    )
    companies_map = {}
    if csv_company_names:
        qs = Company.objects.filter(name__iexact__in=list(csv_company_names)) \
              if False else Company.objects.filter(name__in=list(csv_company_names))
        # above line uses name__in for simplicity; we'll map case-insensitively below

        # Build case-insensitive map:
        for c in Company.objects.filter(name__in=list(csv_company_names)).all():
            companies_map[c.name.strip().lower()] = c

        # If none matched via name__in, try a full DB scan for any missing names (safe fallback)
        if len(companies_map) < len(csv_company_names):
            for c in Company.objects.all():
                lc = c.name.strip().lower()
                if lc in csv_company_names and lc not in companies_map:
                    companies_map[lc] = c

    # Helper validators
    email_re = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    phone_re = re.compile(r'^[0-9]{7,15}$')

    # Validate row-by-row
    for idx, row in enumerate(rows):
        errors = {}
        # Normalize inputs
        first = (row.get('first_name') or '').strip()
        last = (row.get('last_name') or '').strip()
        email = (row.get('email') or '').strip()
        email_lc = email.lower()
        phone = (row.get('phone') or '').strip()
        city = (row.get('city') or '').strip()
        state = (row.get('state') or '').strip()
        country = (row.get('country') or '').strip()
        csv_company = (row.get('company') or '').strip()
        plan = (row.get('plan') or '').strip()

        # 1) Required fields
        if not first:
            errors['first_name'] = 'Required'
        if not email:
            errors['email'] = 'Required'
        if not plan:
            errors['plan'] = 'Required'

        # 2) Email format
        if email:
            if not email_re.match(email):
                errors['email'] = errors.get('email', 'Invalid email format')

        # 3) Duplicate email inside CSV
        if email:
            if csv_emails_lower.count(email_lc) > 1:
                errors['email'] = 'Duplicate email inside CSV'

        # 4) Email already exists in DB
        if email:
            if email_lc in existing_emails:
                # If the DB contains this email, treat as error (do not allow overwrite)
                errors['email'] = 'Email already exists'

        # 5) Phone validation (optional field but validate if present)
        if phone:
            # strip non-digits for validation convenience
            digits = re.sub(r'\D', '', phone)
            if not phone_re.match(digits):
                errors['phone'] = 'Phone must be 7-15 digits'

        # 6) Plan validation
        if plan:
            if plan.strip().lower() not in ['elite', 'core', 'digital']:
                errors['plan'] = 'Plan must be Elite/Core/Digital'

        # 7) Company existence check (company optional; if provided must exist)
        if csv_company:
            c_obj = companies_map.get(csv_company.strip().lower())
            if not c_obj:
                errors['company'] = f"Company '{csv_company}' not found"

        # 8) Length checks (optional, but helpful)
        if first and len(first) > 120:
            errors['first_name'] = 'Too long (max 120 chars)'
        if last and len(last) > 120:
            errors['last_name'] = 'Too long (max 120 chars)'
        if city and len(city) > 120:
            errors['city'] = 'Too long (max 120 chars)'
        if state and len(state) > 120:
            errors['state'] = 'Too long (max 120 chars)'

        # 9) Collect results
        errors_count = len([k for k in errors.keys() if k != '_rowErrorCount'])
        errors['_rowErrorCount'] = errors_count
        total_errors += errors_count
        row_errors.append(errors)

    return row_errors, total_errors

# ---------------------------
# ClientsBulkUploadView: uses validate_csv_rows
# ---------------------------
class ClientsBulkUploadView(APIView):
    """
    GET: render upload page
    POST: validate all rows first using validate_csv_rows, return 400 + rowErrors if any,
          otherwise create all users inside a single atomic transaction.
    """
    def get(self, request):
        return render(request, "accounts/add_bulk_users_page.html")

    def post(self, request):
        # expecting JSON body { rows: [ {first_name,...}, ... ] }
        rows = request.data.get('rows', []) if isinstance(request.data, dict) else []

        # Ensure rows is a list
        if not isinstance(rows, list):
            return Response({"success": False, "message": "Invalid payload, 'rows' must be a list."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------------------
        # 1) Strict server-side validation pass
        # ------------------------------
        row_errors, total_errors = validate_csv_rows(rows, request=request)

        # If any errors -> return 400 plus per-row errors (same array length)
        if total_errors > 0:
            # Ensure row_errors length matches rows length (it should)
            # Respond with requested contract
            return Response({"success": False, "rowErrors": row_errors}, status=status.HTTP_400_BAD_REQUEST)

        # ------------------------------
        # 2) All rows validated: create all users atomically
        # ------------------------------
        created_ids = []
        try:
            with transaction.atomic():
                for row in rows:
                    first = (row.get('first_name') or '').strip()
                    last = (row.get('last_name') or '').strip()
                    email = (row.get('email') or '').strip()
                    phone = (row.get('phone') or '').strip()
                    city = (row.get('city') or '').strip()
                    state = (row.get('state') or '').strip()
                    country = (row.get('country') or '').strip()
                    csv_company = (row.get('company') or '').strip()
                    plan = (row.get('plan') or '').strip()

                    # generate unique username based on email local-part
                    base = email.split('@')[0].lower()
                    username = base
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base}{counter}"
                        counter += 1

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first,
                        last_name=last
                    )

                    # resolve company if provided (case-insensitive)
                    company_obj = None
                    if csv_company:
                        company_obj = Company.objects.filter(name__iexact=csv_company.strip()).first()

                    ClientProfile.objects.create(
                        user=user,
                        phone=phone,
                        city=city,
                        state=state,
                        country=country,
                        company=company_obj,
                        plan=plan.capitalize() if plan else ''
                    )

                    created_ids.append(user.id)

        except Exception as e:
            # Any exception - rollback already triggered by transaction.atomic()
            # Return a 500-like response with some helpful information
            return Response({"success": False, "message": "Server error during creation", "errors": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ------------------------------
        # 3) Success
        # ------------------------------
        return Response({"success": True, "created": created_ids}, status=status.HTTP_200_OK)