from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()

class Customer(models.Model):
    customer_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã khách hàng")
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Khach hang"
        verbose_name_plural = "Khach hang"

    def save(self, *args, **kwargs):
        if not self.customer_code:
            last_customer = Customer.objects.all().order_by('id').last()
            if not last_customer:
                new_id = 1
            else:
                new_id = last_customer.id + 1
            self.customer_code = f"KH{new_id:07d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_code} - {self.full_name}"


class CourtType(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Đang hoạt động"),
        ("INACTIVE", "Ngưng hoạt động"),
    ]

    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã loại sân")
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên loại sân")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE", verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    def save(self, *args, **kwargs):
        if not self.code:
            last_court_type = CourtType.objects.all().order_by('id').last()
            if not last_court_type:
                new_id = 1
            else:
                new_id = last_court_type.id + 1
            self.code = f"LOAISAN{new_id:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Court(models.Model):
    STATUS_CHOICES = [
        ("READY", "Sẵn sàng"),
        ("MAINTENANCE", "Đang bảo trì"),
        ("INACTIVE", "Ngưng hoạt động"),
    ]

    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã sân")
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




class PriceTable(models.Model):
    APPLY_SCOPE_CHOICES = [
        ("ALL", "Tất cả sân"),
        ("SPECIFIC", "Sân cụ thể"),
    ]

    price_table_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã bảng giá")
    price_table_name = models.CharField(max_length=255, unique=True, verbose_name="Tên bảng giá")
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

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.db.models import Q
        
        # 1. Base query for potential overlaps
        overlaps = PriceTable.objects.filter(court_type=self.court_type)
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
            
        # Filter by date range overlap
        date_q = Q(effective_date__lte=self.end_date) if self.end_date else Q()
        date_q &= Q(end_date__gte=self.effective_date) | Q(end_date__isnull=True)
        overlaps = overlaps.filter(date_q)
        
        # 2. Filter by applied days overlap
        final_overlaps = []
        for pt in overlaps:
            if set(self.applied_days or []) & set(pt.applied_days or []):
                # 3. Filter by scope/court overlap
                if self.apply_scope == 'ALL' or pt.apply_scope == 'ALL':
                    final_overlaps.append(pt)
                else:
                    # Both are SPECIFIC, check if they share any courts
                    # Note: This check is only effective if courts are already linked.
                    # For new records, this is handled in the Serializer.
                    pt_courts = set(pt.applied_courts.values_list('court_id', flat=True))
                    # We can't easily check self.applied_courts here for a new record 
                    # because it's not saved yet. 
                    # So we'll keep the Serializer validation as well.
                    pass 
        
        if final_overlaps:
            conflicting_names = ", ".join([pt.price_table_name for pt in final_overlaps])
            raise ValidationError(
                f"Bảng giá này bị trùng lặp thời gian/ngày áp dụng với các bảng giá: {conflicting_names}"
            )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.price_table_code:
            count = PriceTable.objects.count() + 1
            self.price_table_code = f"BG{count:03d}"
        super().save(*args, **kwargs)

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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True,
        verbose_name="Người dùng"
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Sân"
    )
    customer_name = models.CharField(max_length=100, verbose_name="Tên khách hàng", null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại", null=True, blank=True)
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

    # THÊM MỚI: liên kết với Booking
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='qldon_dat',
        null=True,
        blank=True,
        verbose_name="Đặt sân"
    )

    booking_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã đơn đặt")
    ten_khach_hang = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    so_dien_thoai = models.CharField(max_length=20, verbose_name="Số điện thoại")
    gio_bat_dau = models.TimeField(verbose_name="Giờ bắt đầu")
    gio_ket_thuc = models.TimeField(verbose_name="Giờ kết thúc")
    loai_san = models.CharField(max_length=100, verbose_name="Loại sân")
    san_ap_dung = models.CharField(max_length=100, verbose_name="Sân áp dụng")
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
        is_new = self.pk is None

        if self.booking:
            self.ten_khach_hang = self.booking.customer_name or ''
            self.so_dien_thoai = self.booking.phone or ''
            self.gio_bat_dau = self.booking.start_time
            self.gio_ket_thuc = self.booking.end_time
            self.ngay_dat = self.booking.date
            self.tong_tien = self.booking.total_price or 0
            self.ghi_chu = self.booking.notes

            if self.booking.court:
                self.san_ap_dung = self.booking.court.name
                if self.booking.court.court_type:
                    self.loai_san = self.booking.court.court_type.name

            if not self.booking_code:
                count = QLDonDat.objects.count() + 1
                self.booking_code = f"DD{count:05d}"

            # Chỉ lấy trạng thái từ Booking khi tạo đơn mới
            if is_new:
                status_map = {
                    'pending': 'Chờ xác nhận',
                    'confirmed': 'Đã xác nhận',
                    'completed': 'Hoàn thành',
                    'cancelled': 'Hủy',
                }
                self.trang_thai_don = status_map.get(self.booking.status, 'Chờ xác nhận')

        # Tự động cập nhật thanh toán khi đơn hoàn thành
        if self.trang_thai_don == 'Hoàn thành':
            self.thanh_toan = 'Đã thanh toán'

        super().save(*args, **kwargs)

        # Sau khi lưu QLDonDat, đồng bộ ngược lại Booking
        if self.booking:
            reverse_status_map = {
                'Chờ xác nhận': 'pending',
                'Đã xác nhận': 'confirmed',
                'Hoàn thành': 'completed',
                'Hủy': 'cancelled',
            }

            new_booking_status = reverse_status_map.get(self.trang_thai_don)

            if new_booking_status and self.booking.status != new_booking_status:
                self.booking.status = new_booking_status
                self.booking.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"{self.booking_code} - {self.ten_khach_hang}"