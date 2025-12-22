from django.db.models import Case, When, Value, IntegerField
from django.shortcuts import render
from django.http import JsonResponse
from .models import *

# Create your views here.

def admin_users(request):
    return render(request, 'accounts/admin_users.html')

def companies(request):
    return render(request, 'accounts/companies.html')

# @login_required(login_url='login_page')
# def manage_users(request, user_id=None):
#   if request.method == 'GET':
#     if user_id:
#       user = get_object_or_404(User, id=user_id)
#       try:
#         application = get_object_or_404(Application, user=user)
#       except:
#         application = None
#       def get_user_profile(user):
#         profile_data = {}
#         if hasattr(user, 'staffprofile'):
#           profile = user.staffprofile
#           profile_data = {
#             'image_url': profile.image.url if profile.image else None,
#             'gender': profile.gender,
#             'phone': profile.phone,
#           }
#           # Check if a StudentProfile exists for the user
#         elif hasattr(user, 'studentprofile'):
#           profile = user.studentprofile
#           profile_data = {
#             'admission_number': profile.admission_number,
#             'image_url': profile.image.url if profile.image else None,
#             'gender': application.gender,
#             'dob': application.dob,
#             'current_class': profile.current_class.id if profile.current_class else None,
#             'tribe': application.tribe,
#             'gender': application.gender,
#             'dob': application.dob,
#             'parental_situation': application.parental_situation,
#             'street': application.family_street,
#             'ward': application.family_ward,
#             'district': application.family_district,
#             'father_name': application.father_name,
#             'mother_name': application.mother_name,
#             'father_occupation': application.father_occupation,
#             'mother_occupation': application.mother_occupation,
#             'father_email': application.father_email,
#             'mother_email': application.mother_email,
#             'father_phone': application.father_phone,
#             'mother_phone': application.mother_phone,
#             'has_health_insurance': application.has_health_insurance,
#             'insurance_scheme': application.insurance_scheme,
#             'emergency_contact_name': application.emergency_contact_name,
#             'emergency_contact_phone': application.emergency_contact_phone,
#             'first_aid_consent': application.first_aid_consent,
#             'has_allergy': application.has_allergy,
#             'allergy_details': application.allergy_details,
#             'allergy_support': application.allergy_support,
#           }
#         return profile_data
#       user_data = {
#         'id': user.id,
#         'role': [g.name for g in user.groups.all()],
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'profile_data': get_user_profile(user),
#       }
#       return JsonResponse({
#         'success': True,
#         'user': user_data,
#       })
#     else:
#       page = request.GET.get('page', 1)
#       assigned_classes = AssignedClasses.objects.filter(teacher_id=request.user.staffprofile).values_list('class_id', flat=True) if hasattr(request.user, 'staffprofile') else []
#       if request.user.groups.first().name == 'Teacher':
#         users_list = User.objects.filter(studentprofile__current_class__in=assigned_classes).order_by('username')
#       else:
#         users_list = User.objects.all().exclude(Q(id=request.user.id) | Q(is_superuser=True)).order_by('username')
#       paginator = Paginator(users_list, 5)
#       try:
#         users = paginator.page(page)
#       except PageNotAnInteger:
#         users = paginator.page(1)
#       except EmptyPage:
#         users = paginator.page(paginator.num_pages)
#       if request.user.groups.first().name == 'Teacher':
#         # users = User.objects.filter(id__in=users.object_list)
#         user_data = [
#           {
#             "id": user.id,
#             "email": user.email,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "class_name": user.studentprofile.current_class.name if user.studentprofile.current_class else "N/A",
#             "admission_number": user.studentprofile.admission_number,
#             "guardian_name": user.application.father_name if user.application.father_name else user.application.mother_name if user.application.mother_name else user.application.emergency_contact_name if user.application.emergency_contact_name else "N/A",
#             "guardian_phone": user.application.father_phone if user.application.father_phone else user.application.mother_phone if user.application.mother_phone else user.application.emergency_contact_phone if user.application.emergency_contact_phone else "N/A",
#             "last_login": localtime(user.last_login).strftime("%Y-%m-%d %H:%M") if user.last_login else "Never",
#           }
#           for user in users
#         ]
#       else:
#         user_data = [
#           {
#             'id': user.id,
#             'roles': [g.name for g in user.groups.all()],
#             'username': user.username,
#             'email': user.email,
#             'first_name': user.first_name,
#             'last_name': user.last_name,
#             'status': "Active" if user.is_active else "Inactive",
#             'last_login': localtime(user.last_login).strftime("%Y-%m-%d %H:%M") if user.last_login else "Never",
#           } for user in users
#         ]
#       return JsonResponse({
#         'success': True,
#         'users': user_data,
#         'total_students': StudentProfile.objects.all().count(),
#         'total_applications': Application.objects.all().count(),
#         'pagination': {
#           'total_pages': paginator.num_pages,
#           'current_page': users.number,
#           'has_next': users.has_next(),
#           'has_previous': users.has_previous(),
#         }
#       })
#   if request.method == 'POST':
#     if user_id:
#       print("Updating user with ID:", user_id)
#       print("POST data received:", request.POST)
#       user = User.objects.get(id=user_id)
#       if user.groups.first().name == 'Student':
#         print("Fetched user:", user)
#         user.first_name = request.POST.get('firstName')
#         user.last_name = request.POST.get('lastName')
#         user.save()
#         student_profile = StudentProfile.objects.get(user=user)
#         student_profile.current_class = Class.objects.get(id=request.POST.get('currentClass'))
#         # if request.FILES.get('image'):
#         #   student_profile.image = request.FILES.get('image')
#         student_profile.save()
#         application = Application.objects.get(user=user)
#         application.gender = request.POST.get('gender')
#         application.dob = request.POST.get('dob')
#         application.tribe = request.POST.get('tribe')
#         application.parental_situation = request.POST.get('parentalSituation')
#         application.save()
#         # icon = 'pen'
#         # title = 'Student Profile Updated'
#         # description = student_profile.user.get_full_name() + "'s profile was updated."
#         # ActivitiesLog.objects.create(user=request.user, title=title, description=description, icon=icon)
#         return JsonResponse({'success': True})
#       else:
#         user = User.objects.get(id=user_id)
#         user.first_name = request.POST.get('firstName')
#         user.last_name = request.POST.get('lastName')
#         user.save()
#         staff_profile = StaffProfile.objects.get(user=user)
#         staff_profile.gender = request.POST.get('gender') 
#         staff_profile.phone = request.POST.get('phone') if request.POST.get('phone') else None
#         if request.FILES.get('image'):
#           staff_profile.image = request.FILES.get('image')
#         staff_profile.save()
#         # icon = 'pen'
#         # title = 'Staff Profile Updated'
#         # description = staff_profile.user.get_full_name() + "'s profile was updated."
#         # ActivitiesLog.objects.create(user=request.user, title=title, description=description, icon=icon)
#         return JsonResponse({'success': True})
#     else:
#       firstname = request.POST.get('firstname')
#       lastname = request.POST.get('lastname')
#       email = request.POST.get('email')
#       role = request.POST.get('role')
#       password = email.split('@')[0] + '_team_school'  # Default password
#       # Check if email already exists
#       if User.objects.filter(email=email).exists():
#         messages.error(request, 'Email already exists.')
#         return JsonResponse({'success': False, 'error': 'Email already exists.'})
#       try:
#         # Create new user
#         user = User.objects.create_user(
#           username=email.split('@')[0], 
#           first_name=firstname, 
#           last_name=lastname, 
#           email=email,
#           password=password
#         )
#         user.groups.add(Group.objects.get(name=role))
#         user.save()
#         # Create Staff profile
#         StaffProfile.objects.create(user=user)
#         icon = 'user-plus'
#         title = 'New staff member added'
#         description = user.get_full_name() + " - " + role + "."
#         ActivitiesLog.objects.create(user=request.user, title=title, description=description, icon=icon)
#         send_welcome_mail(email)
#         return JsonResponse({'success': True})
#       except Exception as e:
#         messages.error(request, f'Error creating user: {str(e)}')
#         return JsonResponse({'success': False, 'error': str(e)})
#   if request.method == 'DELETE':
#     try:
#       deleted_user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#       return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
#     icon = 'trash'
#     title = 'User Deleted'
#     description = "User " + deleted_user.get_full_name() + " was removed from the system."
#     ActivitiesLog.objects.create(user=request.user, icon=icon, title=title, description=description)
#     deleted_user.delete()
#     return JsonResponse({'success': True})
#   return JsonResponse({'success': False, 'error': 'Invalid request'})

# def manage_users(request):
#   if request.method == 'GET':
#     return JsonResponse({'success': True})
#   if request.method == 'POST':
#     name = request.POST.get("name")
#     email = request.POST.get("email")
#     position = request.POST.get("position")
#     office = request.POST.get("office")

#     if not all([name, email, position, office]):
#         return JsonResponse({"success": False, "error": "All fields are required"})

#     username = email.split("@")[0]

#     if User.objects.filter(username=username).exists():
#         return JsonResponse({
#             "success": False,
#             "error": "User with this email already exists"
#         })

#     user = User.objects.create_user(
#         username=username,
#         email=email,
#         first_name=name,
#     )

#     AdministratorUser.objects.create(
#         user=user,
#     )
#     return JsonResponse({'success': True})

#   return JsonResponse({'success': False, 'error': 'Invalid request'})

# def manage_company(request):
#   if request.method == 'GET':
#     return JsonResponse({'success': True})
#   if request.method == 'POST':
#     # Process form data here
#     pass
#     return JsonResponse({'success': True})

#   return JsonResponse({'success': False, 'error': 'Invalid request'})



from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .forms import *
from .models import *

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def admin_users_list_view(request):
    members = (
        User.objects
        .select_related('profile')
        .prefetch_related('profile__roles')
        .filter(profile__roles__isnull=False)
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

        profile = Profile.objects.create(user=user)
        profile.phone = phone

        roles = Role.objects.filter(code__in=role_codes)
        profile.roles.set(roles)
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)

def admin_user_detail_view(request, user_id):
    user = User.objects.select_related('profile').prefetch_related('profile__roles').get(id=user_id)

    data = {
        'id': user.id,
        'firstname': user.first_name,
        'lastname': user.last_name,
        'email': user.email,
        'phone': user.profile.phone,
        'is_active': user.is_active,
        'roles': list(user.profile.roles.values_list('code', flat=True)),
    }
    return JsonResponse(data)

@require_POST
def admin_user_edit_view(request, pk):
    try:
        print("POST data received for edit:", request.POST)
        user = User.objects.select_related('profile').get(id=pk)

        data = request.POST
        role_codes = data.getlist('roles')
        is_active_str = request.POST.get('is_active', 'True')

        if not role_codes:
            return JsonResponse({'error': 'At least one role is required'}, status=400)

        user.first_name = data.get('firstname', '').strip()
        user.last_name = data.get('lastname', '').strip()
        user.email = data.get('email', '').strip()
        user.is_active = is_active_str == 'True'
        user.save()

        user.profile.phone = data.get('phone', '').strip()
        roles = Role.objects.filter(code__in=role_codes)
        user.profile.roles.set(roles)
        user.profile.save()
        return JsonResponse({'success': True, 'id': user.id})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)

@require_POST
def admin_user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return JsonResponse({'success': True})

def user_profile_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = getattr(user,'profile',None)
    return render(request, 'accounts/user_profile.html', {'user': user, 'profile': profile})

def clients_list_view(request):
    users = (
        User.objects
        .select_related('profile', 'profile__company')
        .filter(profile__roles__isnull=True)
        .exclude(is_superuser=True)
        .annotate(
            has_company=Case(
                When(profile__company__isnull=False, then=Value(0)),
                When(profile__company__isnull=True, then=Value(1)),
                output_field=IntegerField(),
            )
        )
        .order_by('has_company')
        .distinct()
    )
    return render(request, 'accounts/users_page.html', {'users': users})

def add_users_page(request):
    companies = Company.objects.all().order_by('name')
    return render(request, 'accounts/add_users_page.html', {'companies': companies})