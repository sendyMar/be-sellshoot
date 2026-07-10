from django.urls import path

app_name = 'catalog'

urlpatterns = [
    # GET    /api/catalog/products/               — List semua produk user
    # POST   /api/catalog/products/               — Buat produk baru
    # GET    /api/catalog/products/<id>/aliases/   — List alias per produk
    # POST   /api/catalog/match/                  — Cari kecocokan nama produk
    # POST   /api/catalog/match/confirm/          — Konfirmasi kecocokan
    # POST   /api/catalog/match/reject/           — Tolak kecocokan
    # GET    /api/catalog/matching-log/           — Riwayat pemetaan
]
