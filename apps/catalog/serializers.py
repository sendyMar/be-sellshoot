from rest_framework import serializers
from .models import Product, ProductAlias

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'canonical_name', 'sku', 'category', 'cost_price', 'retail_price', 'global_stock', 'created_at']

class ProductAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAlias
        fields = ['id', 'alias_name', 'platform', 'created_by_correction', 'created_at']

class ProductMatchRequestSerializer(serializers.Serializer):
    raw_name = serializers.CharField(max_length=300)
    platform = serializers.ChoiceField(choices=ProductAlias.PLATFORM_CHOICES)

class ProductMatchConfirmSerializer(serializers.Serializer):
    raw_name = serializers.CharField(max_length=300)
    platform = serializers.ChoiceField(choices=ProductAlias.PLATFORM_CHOICES)
    product_id = serializers.IntegerField()
    is_correction = serializers.BooleanField(default=False)
