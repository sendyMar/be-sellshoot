from .models import Screenshot

def save_screenshots(user, image_urls, platform, session_id, tag='order_list'):
    screenshots = []
    for url in image_urls:
        screenshot = Screenshot(
            user=user,
            image_url=url,
            platform=platform,
            upload_session=session_id,
            tag=tag
        )
        screenshots.append(screenshot)
    
    # Bulk create for efficiency
    created_screenshots = Screenshot.objects.bulk_create(screenshots)
    return created_screenshots

def get_today_screenshots(user):
    from django.utils import timezone
    today = timezone.now().date()
    return Screenshot.objects.filter(user=user, uploaded_at__date=today).order_by('-uploaded_at')

def delete_screenshot(user, pk):
    try:
        screenshot = Screenshot.objects.get(pk=pk, user=user)
        screenshot.delete()
        return True
    except Screenshot.DoesNotExist:
        return False
