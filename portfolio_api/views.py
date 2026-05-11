from django.http import JsonResponse


def health_check(_request):
    return JsonResponse({"status": "ok", "message": "Batcave backend online"})


def get_projects(_request):
    return JsonResponse(
        {
            "projects": [
                {
                    "title": "Futuristic Autonomous Tram Technology in Smart Cities",
                    "date": "2025-07-12",
                    "category": "AI",
                }
            ]
        }
    )
