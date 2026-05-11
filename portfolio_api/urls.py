from django.urls import include, path

from .views import get_projects, health_check

urlpatterns = [
    path("api/health", health_check),
    path("api/projects", get_projects),
    path("api/alfred/", include("llm_serving.urls")),
]
