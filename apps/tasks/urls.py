from django.urls import path
from .views import TaskGenerateView, TaskListView, TaskUpdateView, CustomTaskTemplateView

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('generate/', TaskGenerateView.as_view(), name='task-generate'),
    path('custom-template/', CustomTaskTemplateView.as_view(), name='task-custom-template'),
    path('<int:pk>/', TaskUpdateView.as_view(), name='task-update'),
]
