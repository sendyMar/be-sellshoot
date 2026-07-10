from django.urls import path

app_name = 'authentication'

urlpatterns = [
    # POST /api/auth/verify/      — Verifikasi Google user & terbitkan JWT
    # POST /api/auth/refresh/     — Refresh JWT token
    # GET  /api/auth/me/          — Ambil profil user saat ini
]
