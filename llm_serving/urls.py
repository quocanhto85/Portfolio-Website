from django.urls import re_path

from .views import AlfredStatsView, AlfredStreamView

app_name = "llm_serving"

# Match with or without a trailing slash so we never lose POST bodies to
# Django's APPEND_SLASH redirect. Some upstream proxies (Next.js dev, some
# Vercel rewrites) silently strip trailing slashes — the regex absorbs that.
urlpatterns = [
    re_path(r"^chat/?$", AlfredStreamView.as_view(), name="alfred-chat"),
    re_path(r"^stats/?$", AlfredStatsView.as_view(), name="alfred-stats"),
]
