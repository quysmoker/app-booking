from django.urls import path

from dashboard.views import (
    DashboardOverviewView,
    DashboardReportView,
)


urlpatterns = [
    path(
        "",
        DashboardOverviewView.as_view(),
        name="dashboard-overview",
    ),
    path(
        "reports/",
        DashboardReportView.as_view(),
        name="dashboard-report",
    ),
]
