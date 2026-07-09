from django.urls import path
from bookings.views import BookingListCreateView, BookingDetailView

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking-list-create"),
    path("<str:booking_id>/", BookingDetailView.as_view(), name="booking-detail"),
]
