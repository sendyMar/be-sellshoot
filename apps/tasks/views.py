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
            # Convert to date object for applies_to check
            from datetime import datetime
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            parsed_date = timezone.now().date()
            target_date = parsed_date.isoformat()
            
        # Instantiate custom tasks if needed
        from .models import CustomTaskTemplate
        templates = CustomTaskTemplate.objects.filter(user=request.user)
        for t in templates:
            if t.applies_to(parsed_date):
                Task.objects.get_or_create(
                    user=request.user,
                    date=target_date,
                    custom_template=t,
                    defaults={
                        'title': t.title,
                        'description': t.description,
                        'priority': t.priority,
                        'category': 'custom',
                        'platform': 'semua'
                    }
                )
                
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
        description = request.data.get('description')
        
        has_changed = False
        if is_completed is not None:
            task.is_completed = is_completed
            task.completed_at = timezone.now() if is_completed else None
            has_changed = True
            
        if description is not None:
            task.description = description
            has_changed = True
            
        if has_changed:
            task.save()
            
        return Response({'success': True, 'message': 'Task updated successfully'})

class CustomTaskTemplateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .models import CustomTaskTemplate
        title = request.data.get('title')
        description = request.data.get('description', '')
        priority = request.data.get('priority', 'normal')
        recurrence_type = request.data.get('recurrence_type', 'daily')
        weekly_days = request.data.get('weekly_days', [])
        
        if not title:
            return Response({'success': False, 'message': 'Title is required'}, status=400)
            
        template = CustomTaskTemplate.objects.create(
            user=request.user,
            title=title,
            description=description,
            priority=priority,
            recurrence_type=recurrence_type,
            weekly_days=weekly_days
        )
        
        return Response({'success': True, 'message': 'Custom task created successfully', 'id': template.id})
