
from django.urls import path

from dashboard.views import DashboardOverviewView


urlpatterns = [
    path(
        "",
        DashboardOverviewView.as_view(),
        name="dashboard-overview",
    ),
]
