from django.db import models
from django.contrib.auth.models import User

class DailyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_reports')
    date = models.DateField()
    total_orders = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    ai_insight = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Report {self.user.username} - {self.date}"
