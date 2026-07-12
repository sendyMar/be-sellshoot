from django.urls import path
from .views import CalendarStatusView, DailyReportView, StatisticsView

app_name = 'reporting'

urlpatterns = [
    path('calendar-status/', CalendarStatusView.as_view(), name='calendar-status'),
    path('daily/', DailyReportView.as_view(), name='daily-report'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    # POST /api/reporting/snapshot/     — Buat snapshot harian
    # GET  /api/reporting/snapshots/    — List snapshot
    # POST /api/reporting/weekly/       — Generate laporan mingguan
    # GET  /api/reporting/weekly/<id>/  — Detail laporan mingguan
]
