from django.db import models
from django.contrib.auth.models import User

class Screenshot(models.Model):
    PLATFORM_CHOICES = [
        ('shopee', 'Shopee'),
        ('tokopedia', 'Tokopedia'),
        ('instagram', 'Instagram'),
        ('other', 'Lainnya'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    upload_session = models.UUIDField()
    status = models.CharField(max_length=20, default='pending') # pending, processed, failed
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} - {self.upload_session}"
