from django.contrib import admin
from .models import Booking, QLDonDat

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'court', 'date', 'start_time', 'end_time', 'total_price', 'status', 'created_at')
    search_fields = ('customer_name', 'phone', 'court__name')
    list_filter = ('status', 'date', 'court__court_type')
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(QLDonDat)
class QLDonDatAdmin(admin.ModelAdmin):
    list_display = ('booking_code', 'ten_khach_hang', 'so_dien_thoai', 'ngay_dat', 'trang_thai_don', 'thanh_toan')
    search_fields = ('booking_code', 'ten_khach_hang', 'so_dien_thoai')
    list_filter = ('trang_thai_don', 'thanh_toan', 'ngay_dat')
    ordering = ('-ngay_dat', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
