from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Product, ProductAlias
from .serializers import (
    ProductSerializer, ProductAliasSerializer, 
    ProductMatchRequestSerializer, ProductMatchConfirmSerializer
)
from .services import find_product_match, save_product_alias

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)


class ProductAliasListView(generics.ListAPIView):
    serializer_class = ProductAliasSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id, user=self.request.user)
        return product.aliases.all().order_by('-created_at')


class MatchProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            raw_name = serializer.validated_data['raw_name']
            platform = serializer.validated_data['platform']
            
            result = find_product_match(request.user, raw_name, platform)
            return Response(result, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductMatchConfirmSerializer(data=request.data)
        if serializer.is_valid():
            raw_name = serializer.validated_data['raw_name']
            platform = serializer.validated_data['platform']
            product_id = serializer.validated_data['product_id']
            is_correction = serializer.validated_data['is_correction']
            
            # Verify product belongs to user
            product = get_object_or_404(Product, id=product_id, user=request.user)
            
            # Save mapping
            alias = save_product_alias(product.id, raw_name, platform, is_correction)
            
            return Response({"status": "success", "alias_id": alias.id}, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
