from django import forms
from .models import *

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name','city','state','country','ceo','size_of_business','notes']
