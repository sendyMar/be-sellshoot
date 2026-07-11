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


class ScreenshotProcessView(APIView):
    """Trigger AI processing untuk screenshot yang masih pending"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Body (opsional): { "screenshot_ids": [1, 2, 3] }
        Jika kosong, proses semua screenshot pending milik user hari ini
        """
        from .ai_service import process_screenshot
        from .models import Screenshot

        screenshot_ids = request.data.get('screenshot_ids', None)

        if screenshot_ids:
            screenshots = Screenshot.objects.filter(
                user=request.user, id__in=screenshot_ids, status='pending'
            )
        else:
            from django.utils import timezone
            today = timezone.now().date()
            screenshots = Screenshot.objects.filter(
                user=request.user, status='pending', uploaded_at__date=today
            )

        results = []
        errors = []

        import time

        for idx, ss in enumerate(screenshots):
            try:
                # Beri jeda antar request agar tidak menabrak limit API
                if idx > 0:
                    time.sleep(4)
                
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        result = process_screenshot(ss)
                        results.append({
                            'screenshot_id': ss.id,
                            'status': 'processed',
                            'items_count': result.items.count(),
                        })
                        break  # Keluar dari loop retry jika berhasil
                    except Exception as retry_error:
                        error_str = str(retry_error).lower()
                        is_rate_limit = '429' in error_str or 'rate' in error_str or 'limit' in error_str or 'quota' in error_str
                        retry_count += 1
                        if retry_count >= max_retries or not is_rate_limit:
                            raise retry_error
                        # Exponential backoff jika kena rate limit
                        time.sleep(10 * retry_count)
            except Exception as e:
                errors.append({
                    'screenshot_id': ss.id,
                    'status': 'failed',
                    'error': str(e),
                })

        return Response({
            'success': True,
            'message': f'{len(results)} screenshot berhasil diproses, {len(errors)} gagal',
            'data': {
                'processed': results,
                'failed': errors,
            }
        })

class ExtractionTodayView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import ExtractionResult
        from django.utils import timezone
        from .serializers import ExtractionResultSerializer
        
        today = timezone.now().date()
        results = ExtractionResult.objects.filter(
            screenshot__user=request.user, 
            processed_at__date=today
        ).order_by('-processed_at')
        
        serializer = ExtractionResultSerializer(results, many=True)
        return Response({'success': True, 'data': serializer.data})
