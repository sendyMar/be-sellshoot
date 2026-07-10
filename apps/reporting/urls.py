from django.urls import path

app_name = 'reporting'

urlpatterns = [
    # POST /api/reporting/snapshot/     — Buat snapshot harian
    # GET  /api/reporting/snapshots/    — List snapshot
    # POST /api/reporting/weekly/       — Generate laporan mingguan
    # GET  /api/reporting/weekly/<id>/  — Detail laporan mingguan
]
