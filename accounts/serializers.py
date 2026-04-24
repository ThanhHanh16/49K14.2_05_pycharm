from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import serializers

from .models import CustomerProfile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username da ton tai.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email da ton tai.")
        return value

    def validate_phone(self, value):
        if CustomerProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("So dien thoai da ton tai.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        phone = validated_data.pop("phone")
        address = validated_data.pop("address", "")

        user = User.objects.create_user(**validated_data)

        # Thêm user vào group 'customer' nếu có
        group, _ = Group.objects.get_or_create(name="customer")
        user.groups.add(group)

        # Signal may already create profile; update it with mobile registration data.
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        profile.full_name = full_name
        profile.phone = phone
        profile.address = address
        profile.role = CustomerProfile.ROLE_CUSTOMER
        profile.save()

        return user


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email") or attrs.get("username")
        password = attrs.get("password")
        
        if not username_or_email:
            raise serializers.ValidationError("Vui long nhap username hoac email.")

        user = None

        if "@" in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if not user:
            raise serializers.ValidationError("Thong tin dang nhap khong chinh xac.")

        if not user.is_active:
            raise serializers.ValidationError("Tai khoan da bi khoa.")

        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "phone",
            "address",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "username", "email", "role", "created_at", "updated_at"]

    def get_role(self, obj):
        if obj.user.is_superuser:
            return "admin"
        if obj.user.is_staff:
            return "staff"
        return obj.role

    def validate_phone(self, value):
        profile_id = self.instance.id if self.instance else None
        qs = CustomerProfile.objects.filter(phone=value)
        if profile_id:
            qs = qs.exclude(id=profile_id)
        if qs.exists():
            raise serializers.ValidationError("So dien thoai da ton tai.")
        return value
