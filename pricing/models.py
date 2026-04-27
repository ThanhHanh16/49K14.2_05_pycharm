from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

class PriceTable(models.Model):
    APPLY_SCOPE_CHOICES = [
        ("ALL", "Tất cả sân"),
        ("SPECIFIC", "Sân cụ thể"),
    ]

    price_table_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Mã bảng giá")
    price_table_name = models.CharField(max_length=255, unique=True, verbose_name="Tên bảng giá")
    court_type = models.ForeignKey(
        'courts.CourtType',
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
    applied_days = models.JSONField(default=list, blank=True, verbose_name="Ngày áp dụng")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Bang gia"
        verbose_name_plural = "Bang gia"

    def clean(self):
        if self.end_date and self.end_date < self.effective_date:
            raise ValidationError("Ngày kết thúc phải lớn hơn hoặc bằng ngày hiệu lực.")

        overlaps = PriceTable.objects.filter(court_type=self.court_type)
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
            
        date_q = Q(effective_date__lte=self.end_date) if self.end_date else Q()
        date_q &= Q(end_date__gte=self.effective_date) | Q(end_date__isnull=True)
        overlaps = overlaps.filter(date_q)
        
        final_overlaps = []
        for pt in overlaps:
            if set(self.applied_days or []) & set(pt.applied_days or []):
                if self.apply_scope == 'ALL' or pt.apply_scope == 'ALL':
                    final_overlaps.append(pt)
                else:
                    # Specific check logic might need more data than available in model.clean
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
        'courts.Court',
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
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")
            
        if getattr(self, 'price_table_id', None) and self.start_time and self.end_time:
            overlaps = PriceTableTimeSlot.objects.filter(
                price_table_id=self.price_table_id,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            if self.pk:
                overlaps = overlaps.exclude(pk=self.pk)
            if overlaps.exists():
                raise ValidationError("Khung giờ này bị trùng lặp với khung giờ khác trong cùng bảng giá.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.price_table.price_table_code} | {self.start_time} - {self.end_time}"
