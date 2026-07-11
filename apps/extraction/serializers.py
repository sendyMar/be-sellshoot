from rest_framework import serializers
from .models import Screenshot, ExtractionResult, ExtractedItem

class ScreenshotCreateSerializer(serializers.Serializer):
    image_urls = serializers.ListField(
        child=serializers.URLField(max_length=500),
        allow_empty=False
    )
    platform = serializers.ChoiceField(choices=Screenshot.PLATFORM_CHOICES)
    upload_session = serializers.UUIDField()

class ScreenshotReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screenshot
        fields = '__all__'


class ExtractedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedItem
        fields = '__all__'


class ExtractionResultSerializer(serializers.ModelSerializer):
    items = ExtractedItemSerializer(many=True, read_only=True)
    screenshot = ScreenshotReadSerializer(read_only=True)

    class Meta:
        model = ExtractionResult
        fields = '__all__'
