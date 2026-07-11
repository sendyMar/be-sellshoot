from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Task

class TaskGenerateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .ai_task_service import generate_tasks_from_verified_data
        from django.utils import timezone
        
        date_str = request.data.get('date')
        if date_str:
            target_date = date_str
        else:
            target_date = timezone.now().date()
            
        try:
            result = generate_tasks_from_verified_data(request.user, target_date)
            if result.get('success'):
                return Response(result)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.utils import timezone
        
        date_str = request.query_params.get('date')
        if date_str:
            target_date = date_str
        else:
            target_date = timezone.now().date().isoformat()
            
        tasks = Task.objects.filter(user=request.user, date=target_date).order_by('is_completed', '-priority', '-created_at')
        
        # Manual serialization
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'category': task.category,
                'priority': task.priority,
                'platform': task.platform,
                'is_completed': task.is_completed,
            })
            
        return Response({'success': True, 'data': task_list})


class TaskUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        from django.utils import timezone
        from django.shortcuts import get_object_or_404
        
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        is_completed = request.data.get('is_completed')
        if is_completed is not None:
            task.is_completed = is_completed
            task.completed_at = timezone.now() if is_completed else None
            task.save()
            
        return Response({'success': True, 'message': 'Task updated successfully'})
