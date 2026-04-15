from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    ROLE_CUSTOMER = 'customer'
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Khach hang'),
        (ROLE_STAFF, 'Nhan vien'),
        (ROLE_ADMIN, 'Quan tri vien'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ho so khach hang'
        verbose_name_plural = 'Ho so khach hang'

    def __str__(self):
        return self.full_name or self.user.username

