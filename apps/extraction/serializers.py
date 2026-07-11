from rest_framework import serializers
from .models import Screenshot

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
