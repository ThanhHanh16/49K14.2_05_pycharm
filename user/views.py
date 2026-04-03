from rest_framework import viewsets, filters
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer

    # Cấu hình tính năng tìm kiếm khách hàng
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']  # Tìm kiếm theo Tên hoặc SĐT