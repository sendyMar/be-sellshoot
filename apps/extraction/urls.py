from django.urls import path
from .views import ScreenshotUploadView, ScreenshotListView, ScreenshotDeleteView

app_name = 'extraction'

urlpatterns = [
    path('upload/', ScreenshotUploadView.as_view(), name='screenshot_upload'),
    path('screenshots/', ScreenshotListView.as_view(), name='screenshot_list'),
    path('screenshots/<int:pk>/', ScreenshotDeleteView.as_view(), name='screenshot_delete'),
]
