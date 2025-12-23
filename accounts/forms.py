from django import forms
from django.contrib.auth.models import User
from .models import *

class AdminUserForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(queryset=Role.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    phone = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    country = forms.CharField(required=False)
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile, _ = MemberProfile.objects.get_or_create(user=user)
        profile.phone = self.cleaned_data.get('phone','')
        profile.city = self.cleaned_data.get('city','')
        profile.state = self.cleaned_data.get('state','')
        profile.country = self.cleaned_data.get('country','')
        profile.company = self.cleaned_data.get('company')
        if commit:
            profile.save()
            roles = self.cleaned_data.get('roles')
            if roles:
                profile.roles.set(roles)
        return user

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name','city','state','country','ceo','size_of_business','notes']