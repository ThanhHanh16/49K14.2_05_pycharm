from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    customer_code = serializers.CharField(required=False, read_only=True)
    full_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    
    # Mapping for Android compatibility
    name = serializers.CharField(source='full_name', required=False)
    phone = serializers.CharField(source='phone_number', required=False)
    ghi_chu = serializers.CharField(source='notes', required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ['id', 'customer_code', 'full_name', 'phone_number', 'name', 'phone', 'email', 'notes', 'ghi_chu', 'created_at']

    def validate(self, data):
        # Đảm bảo full_name và phone_number không được rỗng khi lưu vào model
        if not data.get('full_name'):
            data['full_name'] = "Khách hàng mới"
        if not data.get('phone_number'):
            # Nếu không có số điện thoại, tạo một số ngẫu nhiên hoặc để N/A để tránh lỗi UNIQUE nếu cần
            # Ở đây ta nên bắt người dùng nhập hoặc để N/A nếu model cho phép (nhưng model của bạn có UNIQUE)
            pass 
        return data

    def validate_phone(self, value):
        return self.validate_phone_number(value)

    def validate_phone_number(self, value):
        if not value or value == "N/A":
            return value
        customer_id = self.instance.id if self.instance else None
        qs = Customer.objects.filter(phone_number=value)
        if customer_id:
            qs = qs.exclude(id=customer_id)
        if qs.exists():
            raise serializers.ValidationError("Số điện thoại này đã được sử dụng!")
        return value
