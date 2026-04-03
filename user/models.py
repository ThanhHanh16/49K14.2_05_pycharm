from django.db import models
from django.core.exceptions import ValidationError

class Customer(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Khach hang"
        verbose_name_plural = "Khach hang"

    def __str__(self):
        return self.full_name




class LoaiSan(models.Model):
    ten_loai_san = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Loai san"
        verbose_name_plural = "Loai san"

    def __str__(self):
        return self.ten_loai_san


class San(models.Model):
    ma_san = models.CharField(max_length=20, unique=True)
    ten_san = models.CharField(max_length=100)
    loai_san = models.ForeignKey(LoaiSan, on_delete=models.CASCADE, related_name='ds_san')
    dang_hoat_dong = models.BooleanField(default=True)

    class Meta:
        verbose_name = "San"
        verbose_name_plural = "San"

    def __str__(self):
        return f"{self.ma_san} - {self.ten_san}"


class BangGia(models.Model):
    PHAM_VI_CHOICES = [
        ('ALL', 'Tất cả sân'),
        ('SPECIFIC', 'Sân cụ thể'),
    ]

    ma_bang_gia = models.CharField(max_length=20, unique=True)
    ten_bang_gia = models.CharField(max_length=255)
    loai_san = models.ForeignKey(LoaiSan, on_delete=models.CASCADE, related_name='bang_gia')
    pham_vi_ap_dung = models.CharField(max_length=10, choices=PHAM_VI_CHOICES, default='ALL')

    ngay_hieu_luc = models.DateField()
    ngay_ket_thuc = models.DateField(null=True, blank=True)

    # Lưu các ngày áp dụng: ["T2", "T3", "T4", "T5", "T6"] hoặc ["T7", "CN"]
    ngay_ap_dung = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bang gia"
        verbose_name_plural = "Bang gia"

    def clean(self):
        if self.ngay_ket_thuc and self.ngay_ket_thuc < self.ngay_hieu_luc:
            raise ValidationError("Ngày kết thúc phải lớn hơn hoặc bằng ngày hiệu lực.")

    def __str__(self):
        return f"{self.ma_bang_gia} - {self.ten_bang_gia}"


class BangGiaSanApDung(models.Model):
    bang_gia = models.ForeignKey(BangGia, on_delete=models.CASCADE, related_name='san_ap_dung')
    san = models.ForeignKey(San, on_delete=models.CASCADE, related_name='bang_gia_ap_dung')

    class Meta:
        unique_together = ('bang_gia', 'san')
        verbose_name = "Bang gia san ap dung"
        verbose_name_plural = "Bang gia san ap dung"

    def __str__(self):
        return f"{self.bang_gia.ma_bang_gia} - {self.san.ten_san}"


class KhungGioBangGia(models.Model):
    bang_gia = models.ForeignKey(BangGia, on_delete=models.CASCADE, related_name='khung_gio')
    gio_bat_dau = models.TimeField()
    gio_ket_thuc = models.TimeField()
    don_gia = models.DecimalField(max_digits=12, decimal_places=0)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)
    thu_tu = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['thu_tu', 'gio_bat_dau']
        verbose_name = "Khung gio bang gia"
        verbose_name_plural = "Khung gio bang gia"

    def clean(self):
        if self.gio_ket_thuc <= self.gio_bat_dau:
            raise ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")

    def __str__(self):
        return f"{self.bang_gia.ma_bang_gia} | {self.gio_bat_dau} - {self.gio_ket_thuc}"