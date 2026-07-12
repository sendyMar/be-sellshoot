from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import GoogleAuthVerifyView, UserMeView

app_name = 'authentication'

urlpatterns = [
    path('verify/', GoogleAuthVerifyView.as_view(), name='google_auth_verify'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserMeView.as_view(), name='user_me'),
]
