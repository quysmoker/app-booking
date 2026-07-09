from django.urls import path
from courts.views import CourtListCreateView, CourtDetailView

urlpatterns = [
    path("", CourtListCreateView.as_view(), name="court-list-create"),
    path("<str:court_id>/", CourtDetailView.as_view(), name="court-detail"),
]
