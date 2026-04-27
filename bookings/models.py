from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
        ('completed', 'Đã hoàn thành'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True,
        verbose_name="Người dùng"
    )
    court = models.ForeignKey(
        'courts.Court',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Sân"
    )
    customer_name = models.CharField(max_length=100, verbose_name="Tên khách hàng", null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại", null=True, blank=True)
    date = models.DateField(verbose_name="Ngày đặt")
    start_time = models.TimeField(verbose_name="Giờ bắt đầu")
    end_time = models.TimeField(verbose_name="Giờ kết thúc")
    total_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Trạng thái"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    order = models.ForeignKey(
        'QLDonDat',
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True,
        verbose_name="Đơn hàng"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Dat san"
        verbose_name_plural = "Dat san"
        ordering = ['-date', '-created_at']
        unique_together = ['court', 'date', 'start_time', 'end_time']

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")

    def __str__(self):
        return f"{self.customer_name} - {self.court.name} - {self.date} {self.start_time}-{self.end_time}"


class QLDonDat(models.Model):
    STATUS_CHOICES = [
        ('Chờ xác nhận', 'Chờ xác nhận'),
        ('Đã xác nhận', 'Đã xác nhận'),
        ('Hoàn thành', 'Hoàn thành'),
        ('Hủy', 'Hủy'),
    ]

    PAYMENT_CHOICES = [
        ('Đã thanh toán', 'Đã thanh toán'),
        ('Chưa thanh toán', 'Chưa thanh toán'),
    ]

    booking_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã đơn đặt")
    ten_khach_hang = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    so_dien_thoai = models.CharField(max_length=20, verbose_name="Số điện thoại")
    gio_bat_dau = models.TimeField(verbose_name="Giờ bắt đầu")
    gio_ket_thuc = models.TimeField(verbose_name="Giờ kết thúc")
    loai_san = models.CharField(max_length=255, verbose_name="Loại sân")
    san_ap_dung = models.CharField(max_length=255, verbose_name="Sân áp dụng")
    ngay_dat = models.DateField(verbose_name="Ngày đặt")
    tong_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền")
    trang_thai_don = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Chờ xác nhận',
        verbose_name="Trạng thái đơn"
    )
    thanh_toan = models.CharField(
        max_length=50,
        choices=PAYMENT_CHOICES,
        default='Chưa thanh toán',
        verbose_name="Thanh toán"
    )
    ghi_chu = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Quản lý đơn đặt"
        verbose_name_plural = "Quản lý đơn đặt"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_code:
            count = QLDonDat.objects.count() + 1
            self.booking_code = f"DD{count:05d}"

        if self.trang_thai_don == 'Hoàn thành':
            self.thanh_toan = 'Đã thanh toán'

        super().save(*args, **kwargs)

        reverse_status_map = {
            'Chờ xác nhận': 'pending',
            'Đã xác nhận': 'confirmed',
            'Hoàn thành': 'completed',
            'Hủy': 'cancelled',
        }

        new_booking_status = reverse_status_map.get(self.trang_thai_don)

        if new_booking_status:
            self.bookings.exclude(status=new_booking_status).update(status=new_booking_status)

    def __str__(self):
        return f"{self.booking_code} - {self.ten_khach_hang}"
