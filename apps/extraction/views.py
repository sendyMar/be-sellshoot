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
            tag = serializer.validated_data.get('tag', 'order_list')

            save_screenshots(request.user, image_urls, platform, upload_session, tag)
            
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

class ExtractionReviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from .models import ExtractedItem
            from django.utils import timezone
            
            date_str = request.query_params.get('date', None)
            if date_str:
                from datetime import datetime
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                target_date = timezone.now().date()
                
            results = ExtractedItem.objects.filter(
                extraction_result__screenshot__user=request.user, 
                extraction_result__processed_at__date=target_date,
                is_verified=False
            ).select_related('extraction_result__screenshot', 'matched_product')
            
            auto_verified = []
            needs_review = []
            
            for res in results:
                screenshot = res.extraction_result.screenshot
                item_data = {
                    'id': res.id,
                    'screenshot_url': request.build_absolute_uri(screenshot.image_url) if screenshot.image_url.startswith('/') else screenshot.image_url,
                    'product_name': res.product_name,
                    'quantity': res.quantity,
                    'price': res.price,
                    'status': res.status,
                    'confidence': float(res.confidence),
                    'matched_product': {
                        'id': res.matched_product.id,
                        'canonical_name': res.matched_product.canonical_name,
                    } if res.matched_product else None
                }
                
                if res.confidence >= 0.85 and res.matched_product:
                    auto_verified.append(item_data)
                else:
                    needs_review.append(item_data)
                    
            return Response({
                'success': True,
                'data': {
                    'auto_verified': auto_verified,
                    'needs_review': needs_review
                }
            })
        except Exception as e:
            import traceback
            return Response({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}, status=500)

class ExtractionReviewVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .models import ExtractedItem
        
        item_ids = request.data.get('item_ids', [])
        corrections = request.data.get('corrections', [])
        
        # Verify selected items
        ExtractedItem.objects.filter(
            extraction_result__screenshot__user=request.user,
            id__in=item_ids
        ).update(is_verified=True)
        
        # Apply corrections if any
        for corr in corrections:
            try:
                item = ExtractedItem.objects.get(id=corr['id'], extraction_result__screenshot__user=request.user)
                if 'matched_product_id' in corr:
                    item.matched_product_id = corr['matched_product_id']
                if 'product_name' in corr:
                    item.product_name = corr['product_name']
                item.is_verified = True
                item.save()
            except ExtractedItem.DoesNotExist:
                continue
                
        return Response({'success': True, 'message': 'Verification complete'})
