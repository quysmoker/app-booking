# from django.urls import path

# from dashboard.views import (
#     DashboardBookingReportView,
#     DashboardOrderReportView,
#     DashboardOverviewView,
#     DashboardRecentActivityView,
#     DashboardRevenueView,
# )


# urlpatterns = [
#     path(
#         "overview/",
#         DashboardOverviewView.as_view(),
#         name="dashboard-overview",
#     ),
#     path(
#         "revenue/",
#         DashboardRevenueView.as_view(),
#         name="dashboard-revenue",
#     ),
#     path(
#         "bookings/",
#         DashboardBookingReportView.as_view(),
#         name="dashboard-booking-report",
#     ),
#     path(
#         "orders/",
#         DashboardOrderReportView.as_view(),
#         name="dashboard-order-report",
#     ),
#     path(
#         "recent-activity/",
#         DashboardRecentActivityView.as_view(),
#         name="dashboard-recent-activity",
#     ),
# ]

from django.urls import path

from dashboard.views import DashboardOverviewView


urlpatterns = [
    path(
        "",
        DashboardOverviewView.as_view(),
        name="dashboard-overview",
    ),
]
