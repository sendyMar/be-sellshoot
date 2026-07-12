from django.db import models
from django.contrib.auth.models import User

class Screenshot(models.Model):
    PLATFORM_CHOICES = [
        ('shopee', 'Shopee'),
        ('tokopedia', 'Tokopedia'),
        ('instagram', 'Instagram'),
        ('other', 'Lainnya'),
    ]
    TAG_CHOICES = [
        ('order_list', 'Daftar Pesanan'),
        ('order_detail', 'Detail Pesanan'),
        ('product_stock', 'Stok Produk'),
        ('chat', 'Chat Pelanggan'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    tag = models.CharField(max_length=50, choices=TAG_CHOICES, default='order_list')
    upload_session = models.UUIDField()
    status = models.CharField(max_length=20, default='pending') # pending, processed, failed
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} ({self.tag}) - {self.upload_session}"


class ExtractionResult(models.Model):
    """Hasil ekstraksi AI dari satu screenshot"""
    screenshot = models.ForeignKey(Screenshot, on_delete=models.CASCADE, related_name='results')
    raw_ai_response = models.JSONField(null=True, blank=True)  # Backup respons mentah Gemini
    narrative = models.TextField(blank=True, null=True)        # Narasi / konteks hasil ekstraksi
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Extraction for Screenshot {self.screenshot_id}"


class ExtractedItem(models.Model):
    STATUS_CHOICES = [
        ('perlu_tindakan', 'Perlu Tindakan'),
        ('diproses', 'Diproses'),
        ('selesai', 'Selesai'),
        ('dikirim', 'Dikirim'),
        ('dibatalkan', 'Dibatalkan'),
        ('lainnya', 'Lainnya'),
    ]
    extraction_result = models.ForeignKey(ExtractionResult, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=300)         # Nama PERSIS dari screenshot
    quantity = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='lainnya')
    order_id = models.CharField(max_length=100, null=True, blank=True)
    buyer_name = models.CharField(max_length=200, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    confidence = models.FloatField(default=0.0)              # 0.0 - 1.0
    is_verified = models.BooleanField(default=False)         # Dikonfirmasi user?
    matched_product = models.ForeignKey(                     # Link ke katalog (setelah matching)
        'catalog.Product', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='extracted_items'
    )

    def __str__(self):
        return f"{self.product_name} ({self.status})"
