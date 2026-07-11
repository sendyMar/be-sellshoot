from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
        ('low', 'Low')
    ]
    CATEGORY_CHOICES = [
        ('order', 'Proses Order'),
        ('restock', 'Restock'),
        ('reply_chat', 'Balas Chat'),
        ('packing', 'Packing'),
        ('other', 'Lainnya'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    date = models.DateField(auto_now_add=True)  # Tanggal task dibuat
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    platform = models.CharField(max_length=50, default='semua')
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"
