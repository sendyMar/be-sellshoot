from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth.models import User
from .models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
import os

def verify_or_create_user(token):
    try:
        # Verify the token
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # ID token is valid.
        google_id = idinfo['sub']
        email = idinfo.get('email', '')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        # Check if user exists by google_id
        userprofile = UserProfile.objects.filter(google_id=google_id).first()
        
        if userprofile:
            user = userprofile.user
        else:
            # Create user
            # Fallback to a unique username if email is already taken but not linked
            username = email if email else f"google_{google_id}"
            user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'first_name': name})
            
            # Create profile
            UserProfile.objects.create(
                user=user,
                google_id=google_id,
                avatar_url=picture
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.first_name,
                'avatar': user.userprofile.avatar_url
            }
        }

    except ValueError as e:
        # Invalid token
        print(f"Token validation error: {e}")
        return None
