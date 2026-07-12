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
        ('custom', 'Custom Task'),
        ('other', 'Lainnya'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    date = models.DateField(auto_now_add=True)  # Tanggal task dibuat
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    platform = models.CharField(max_length=50, default='semua')
    custom_template = models.ForeignKey('CustomTaskTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"

class CustomTaskTemplate(models.Model):
    RECURRENCE_CHOICES = [
        ('daily', 'Setiap Hari'),
        ('weekly', 'Pilih Hari Dalam Seminggu'),
        ('monthly_end', 'Akhir Bulan'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_task_templates')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='normal')
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='daily')
    weekly_days = models.JSONField(default=list, blank=True)  # List of integers: 0=Mon, 6=Sun
    created_at = models.DateTimeField(auto_now_add=True)

    def applies_to(self, target_date):
        if self.recurrence_type == 'daily':
            return True
        elif self.recurrence_type == 'weekly':
            return target_date.weekday() in self.weekly_days
        elif self.recurrence_type == 'monthly_end':
            import calendar
            last_day = calendar.monthrange(target_date.year, target_date.month)[1]
            return target_date.day == last_day
        return False

    def __str__(self):
        return f"Template: {self.title} ({self.recurrence_type})"
