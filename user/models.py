from django.core.exceptions import ValidationError
from django.db import models


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


class CourtType(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Đang hoạt động"),
        ("INACTIVE", "Ngưng hoạt động"),
    ]

    DURATION_CHOICES = [
        (60, "60 phút"),
        (90, "90 phút"),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Mã loại sân")
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên loại sân")
    duration = models.IntegerField(choices=DURATION_CHOICES, verbose_name="Thời lượng")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE", verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    def __str__(self):
        return self.name


class Court(models.Model):
    STATUS_CHOICES = [
        ("READY", "Sẵn sàng"),
        ("MAINTENANCE", "Đang bảo trì"),
        ("INACTIVE", "Ngưng hoạt động"),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Mã sân")
    name = models.CharField(max_length=100, verbose_name="Tên sân")
    court_type = models.ForeignKey(
        CourtType,
        on_delete=models.PROTECT,
        related_name="courts",
        verbose_name="Loại sân"
    )
    area = models.CharField(max_length=50, blank=True, null=True, verbose_name="Khu vực")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="READY", verbose_name="Trạng thái sân")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    def __str__(self):
        return self.name


class PriceTable(models.Model):
    APPLY_SCOPE_CHOICES = [
        ("ALL", "Tất cả sân"),
        ("SPECIFIC", "Sân cụ thể"),
    ]

    price_table_code = models.CharField(max_length=20, unique=True, verbose_name="Mã bảng giá")
    price_table_name = models.CharField(max_length=255, verbose_name="Tên bảng giá")
    court_type = models.ForeignKey(
        CourtType,
        on_delete=models.CASCADE,
        related_name="price_tables",
        verbose_name="Loại sân"
    )
    apply_scope = models.CharField(
        max_length=10,
        choices=APPLY_SCOPE_CHOICES,
        default="ALL",
        verbose_name="Phạm vi áp dụng"
    )

    effective_date = models.DateField(verbose_name="Ngày hiệu lực")
    end_date = models.DateField(null=True, blank=True, verbose_name="Ngày kết thúc")

    # Ví dụ: ["T2", "T3", "T4", "T5", "T6"] hoặc ["T7", "CN"]
    applied_days = models.JSONField(default=list, blank=True, verbose_name="Ngày áp dụng")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Bang gia"
        verbose_name_plural = "Bang gia"

    def clean(self):
        if self.end_date and self.end_date < self.effective_date:
            raise ValidationError("Ngày kết thúc phải lớn hơn hoặc bằng ngày hiệu lực.")

    def __str__(self):
        return f"{self.price_table_code} - {self.price_table_name}"


class PriceTableCourt(models.Model):
    price_table = models.ForeignKey(
        PriceTable,
        on_delete=models.CASCADE,
        related_name="applied_courts",
        verbose_name="Bảng giá"
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name="price_table_links",
        verbose_name="Sân"
    )

    class Meta:
        unique_together = ("price_table", "court")
        verbose_name = "Bang gia san ap dung"
        verbose_name_plural = "Bang gia san ap dung"

    def __str__(self):
        return f"{self.price_table.price_table_code} - {self.court.name}"


class PriceTableTimeSlot(models.Model):
    price_table = models.ForeignKey(
        PriceTable,
        on_delete=models.CASCADE,
        related_name="time_slots",
        verbose_name="Bảng giá"
    )
    start_time = models.TimeField(verbose_name="Giờ bắt đầu")
    end_time = models.TimeField(verbose_name="Giờ kết thúc")
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Đơn giá")
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ghi chú")
    order = models.PositiveIntegerField(default=1, verbose_name="Thứ tự")

    class Meta:
        ordering = ["order", "start_time"]
        verbose_name = "Khung gio bang gia"
        verbose_name_plural = "Khung gio bang gia"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")

    def __str__(self):
        return f"{self.price_table.price_table_code} | {self.start_time} - {self.end_time}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
        ('completed', 'Đã hoàn thành'),
    ]

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Sân"
    )
    customer_name = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    date = models.DateField(verbose_name="Ngày đặt")
    start_time = models.TimeField(verbose_name="Giờ bắt đầu")
    end_time = models.TimeField(verbose_name="Giờ kết thúc")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Trạng thái"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Dat san"
        verbose_name_plural = "Dat san"
        ordering = ['-date', '-created_at']
        # Đảm bảo không trùng lặp đặt sân cùng thời gian
        unique_together = ['court', 'date', 'start_time', 'end_time']

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")

    def __str__(self):
        return f"{self.customer_name} - {self.court.name} - {self.date} {self.start_time}-{self.end_time}"
