from django.urls import path
from .views import ProductListCreateView, ProductAliasListView, MatchProductView, ConfirmMatchView

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:product_id>/aliases/', ProductAliasListView.as_view(), name='product-alias-list'),
    path('match/', MatchProductView.as_view(), name='match-product'),
    path('match/confirm/', ConfirmMatchView.as_view(), name='confirm-match'),
]
