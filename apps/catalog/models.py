from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """Master data produk milik user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    canonical_name = models.CharField(max_length=300)
    sku = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'canonical_name']

    def __str__(self):
        return self.canonical_name


class ProductAlias(models.Model):
    """
    Pemetaan nama produk lintas platform ke satu Product master.
    Berfungsi sekaligus sebagai 'memory' / alias log —
    setiap kali user mengkonfirmasi bahwa 'Long Tail Shoes Prem' = 'Sepatu Premium',
    alias disimpan di sini agar hari berikutnya langsung auto-verify.
    """
    PLATFORM_CHOICES = [
        ('shopee', 'Shopee'),
        ('tokopedia', 'Tokopedia'),
        ('instagram', 'Instagram'),
        ('other', 'Lainnya'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='aliases')
    alias_name = models.CharField(max_length=300)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    created_by_correction = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'alias_name', 'platform']

    def __str__(self):
        return f"{self.alias_name} → {self.product.canonical_name}"
