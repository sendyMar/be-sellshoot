from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    canonical_name = models.CharField(max_length=300)
    sku = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    cost_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    global_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'canonical_name']

    def __str__(self):
        return self.canonical_name


class ProductAlias(models.Model):
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
        return f"{self.alias_name} ({self.platform})"
