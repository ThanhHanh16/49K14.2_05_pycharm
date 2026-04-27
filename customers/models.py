from django.db import models

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
