from django.urls import path

from .views import get_projects, health_check

urlpatterns = [
    path("api/health", health_check),
    path("api/projects", get_projects),
]
