from django.http import JsonResponse


def health_check(_request):
    return JsonResponse({"status": "ok", "message": "Batcave backend online"})


def get_projects(_request):
    return JsonResponse(
        {
            "projects": [
                {
                    "title": "Teaching Qwen to do better translation via fine-tuning",
                    "date": "2026-04-15",
                    "category": "AI",
                },
                {
                    "title": "Document Search Agent",
                    "date": "2026-03-28",
                    "category": "RAG",
                },
                {
                    "title": "LLM Code Execution Agent",
                    "date": "2026-03-22",
                    "category": "Agents",
                },
            ]
        }
    )
