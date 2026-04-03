from django.db import models

class Customer(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name