from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import ScreenshotCreateSerializer, ScreenshotReadSerializer
from .services import save_screenshots, get_today_screenshots, delete_screenshot

class ScreenshotUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScreenshotCreateSerializer(data=request.data)
        if serializer.is_valid():
            image_urls = serializer.validated_data['image_urls']
            platform = serializer.validated_data['platform']
            upload_session = serializer.validated_data['upload_session']

            save_screenshots(request.user, image_urls, platform, upload_session)
            
            return Response({'success': True, 'message': 'Screenshots saved successfully'}, status=status.HTTP_201_CREATED)
        
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ScreenshotListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        screenshots = get_today_screenshots(request.user)
        serializer = ScreenshotReadSerializer(screenshots, many=True)
        return Response({'success': True, 'data': serializer.data})

class ScreenshotDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        success = delete_screenshot(request.user, pk)
        if success:
            return Response({'success': True, 'message': 'Screenshot deleted'})
        return Response({'success': False, 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
