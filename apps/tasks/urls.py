from django.urls import path
from .views import TaskGenerateView, TaskListView, TaskUpdateView

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('generate/', TaskGenerateView.as_view(), name='task-generate'),
    path('<int:pk>/', TaskUpdateView.as_view(), name='task-update'),
]
