from django.urls import path

app_name = 'tasks'

urlpatterns = [
    # POST  /api/tasks/generate/    — Generate task dari data verified
    # GET   /api/tasks/             — List task (filterable)
    # PATCH /api/tasks/<id>/        — Toggle status task
    # GET   /api/tasks/summary/     — Ringkasan task hari ini
]
