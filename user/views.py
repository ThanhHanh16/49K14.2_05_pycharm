from rest_framework import viewsets, filters
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework import viewsets
from .models import LoaiSan, San, BangGia
from .serializers import LoaiSanSerializer, SanSerializer, BangGiaSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer

    # Cấu hình tính năng tìm kiếm khách hàng
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']  # Tìm kiếm theo Tên hoặc SĐT


class LoaiSanViewSet(viewsets.ModelViewSet):
    queryset = LoaiSan.objects.all()
    serializer_class = LoaiSanSerializer


class SanViewSet(viewsets.ModelViewSet):
    queryset = San.objects.select_related('loai_san').all()
    serializer_class = SanSerializer


class BangGiaViewSet(viewsets.ModelViewSet):
    queryset = BangGia.objects.select_related('loai_san').prefetch_related('khung_gio', 'san_ap_dung__san').all()
    serializer_class = BangGiaSerializer