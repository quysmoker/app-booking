from django.urls import path

from bookings.views import (
    BookingDetailView,
    BookingListCreateView,
    BookingStatusUpdateView,
)


urlpatterns = [
    path(
        "",
        BookingListCreateView.as_view(),
        name="booking-list-create",
    ),
    path(
        "<str:booking_id>/status/",
        BookingStatusUpdateView.as_view(),
        name="booking-status-update",
    ),
    path(
        "<str:booking_id>/",
        BookingDetailView.as_view(),
        name="booking-detail",
    ),
]
