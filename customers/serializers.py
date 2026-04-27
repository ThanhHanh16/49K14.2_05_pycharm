from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    customer_code = serializers.CharField(required=False, read_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(source='full_name', required=False, allow_blank=True)
    phone = serializers.CharField(source='phone_number', required=False, allow_blank=True)
    ghi_chu = serializers.CharField(source='notes', required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ['id', 'customer_code', 'full_name', 'phone_number', 'name', 'phone', 'email', 'notes', 'ghi_chu', 'created_at']

    def validate_phone(self, value):
        if not value:
            return value
        customer_id = self.instance.id if self.instance else None
        qs = Customer.objects.filter(phone_number=value)
        if customer_id:
            qs = qs.exclude(id=customer_id)
        if qs.exists():
            raise serializers.ValidationError("Số điện thoại này đã được sử dụng!")
        return value
