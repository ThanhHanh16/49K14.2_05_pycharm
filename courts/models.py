from django.db import models

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
            last = CourtType.objects.all().order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.code = f"LS{new_id:03d}"
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

    def save(self, *args, **kwargs):
        if not self.code:
            last = Court.objects.all().order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.code = f"S{new_id:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"
