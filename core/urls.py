"""
URL configuration for core project.
Routes all API endpoints to their respective app modules.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/extraction/', include('apps.extraction.urls')),
    path('api/catalog/', include('apps.catalog.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/reporting/', include('apps.reporting.urls')),
]
