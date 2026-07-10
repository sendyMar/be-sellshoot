from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GoogleAuthSerializer
from .services import verify_or_create_user
from rest_framework.permissions import IsAuthenticated

class GoogleAuthVerifyView(APIView):
    authentication_classes = [] 
    permission_classes = []
    
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            id_token = serializer.validated_data['id_token']
            auth_data = verify_or_create_user(id_token)
            
            if auth_data:
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'data': auth_data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid Google ID token',
                    'error_code': 'INVALID_TOKEN',
                    'data': None
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        return Response({
            'success': False,
            'message': 'Invalid request data',
            'error_code': 'VALIDATION_ERROR',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'success': True,
            'message': 'User data retrieved',
            'data': {
                'id': user.id,
                'email': user.email,
                'name': user.first_name,
                'avatar': user.userprofile.avatar_url if hasattr(user, 'userprofile') else ''
            }
        })
