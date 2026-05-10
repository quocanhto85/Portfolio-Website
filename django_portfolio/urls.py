from django.urls import include, path

urlpatterns = [
    path("", include("portfolio_api.urls")),
]
