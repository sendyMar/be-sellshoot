from django.urls import path

app_name = 'extraction'

urlpatterns = [
    # POST   /api/extraction/upload/              — Upload screenshot (multi-file)
    # GET    /api/extraction/screenshots/          — List screenshot hari ini
    # DELETE /api/extraction/screenshots/<id>/     — Hapus screenshot
    # POST   /api/extraction/process/              — Proses screenshot dengan Gemini
    # GET    /api/extraction/results/<id>/         — Hasil ekstraksi per screenshot
    # GET    /api/extraction/today/                — Semua hasil ekstraksi hari ini
    # GET    /api/extraction/review/               — Data review (grouped by confidence)
    # POST   /api/extraction/review/verify/        — Batch verifikasi/koreksi
]
