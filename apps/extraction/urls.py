from django.urls import path
from .views import (
    ScreenshotUploadView, 
    ScreenshotListView, 
    ScreenshotDeleteView, 
    ScreenshotProcessView, 
    ExtractionTodayView,
    ExtractionReviewView,
    ExtractionReviewVerifyView
)

app_name = 'extraction'

urlpatterns = [
    path('upload/', ScreenshotUploadView.as_view(), name='screenshot_upload'),
    path('screenshots/', ScreenshotListView.as_view(), name='screenshot_list'),
    path('screenshots/<int:pk>/', ScreenshotDeleteView.as_view(), name='screenshot_delete'),
    path('process/', ScreenshotProcessView.as_view(), name='screenshot_process'),
    path('today/', ExtractionTodayView.as_view(), name='extraction_today'),
    path('review/', ExtractionReviewView.as_view(), name='extraction_review'),
    path('review/verify/', ExtractionReviewVerifyView.as_view(), name='extraction_review_verify'),
]
