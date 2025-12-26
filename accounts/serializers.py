# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from companies.models import *
from .models import *
import re

class ClientsCSVSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=120)
    last_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    plan = serializers.CharField(required=False, allow_blank=True)

    # ------------------- VALIDATIONS -------------------

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name is required")
        if len(value) < 2:
            raise serializers.ValidationError("Too short")
        return value

    def validate_email(self, value):
        value = value.strip()

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise serializers.ValidationError("Invalid email format")

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")

        duplicate_emails = self.context.get("duplicate_emails", [])
        if value.lower() in duplicate_emails:
            raise serializers.ValidationError("Duplicate email inside CSV")

        return value

    def validate_phone(self, value):
        value = value.strip()
        if value and not re.fullmatch(r"[0-9]{7,15}", value):
            raise serializers.ValidationError("Phone must be 7-15 digits")
        return value

    def validate_plan(self, value):
        value = value.strip().capitalize()
        if value and value not in ['Elite','Core','Digital']:
            raise serializers.ValidationError("Plan must be Elite/Core/Digital")
        return value

    def validate_company(self, value):
        value = value.strip() if value else ""

        # scenario: no CSV company + no forced company → OK
        if not value:
            return ""

        # CSV given company, require DB match
        if not Company.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Company not found")

        return value

    # ------------------- CREATE USER & PROFILE -------------------

    def create(self, validated):
        email = validated['email']
        username = email.split('@')[0].lower()

        # generate unique username
        base = username
        count = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{count}"
            count += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=validated['first_name'],
            last_name=validated.get('last_name', '')
        )

        # ---------------- COMPANY SELECTION LOGIC ----------------
        company_name = validated.get('company') or ""
        company_obj = Company.objects.filter(name__iexact=company_name).first() if company_name else None

        # ---------------- CREATE PROFILE --------------------------
        return ClientProfile.objects.create(
            user=user,
            company=company_obj,                                            # <── final result
            plan=validated.get('plan', ''),
            phone=validated.get('phone', ''),
            city=validated.get('city', ''),
            state=validated.get('state', ''),
            country=validated.get('country', ''),
            created_by=self.context['request'].user if self.context['request'].user.is_authenticated else None,
        )
