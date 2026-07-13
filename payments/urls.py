from django.urls import path

from payments.views import (
    PaymentConfirmView,
    PaymentDetailView,
    PaymentFailView,
    PaymentListCreateView,
)


urlpatterns = [
    path(
        "",
        PaymentListCreateView.as_view(),
        name="payment-list-create",
    ),
    path(
        "<str:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "<str:payment_id>/confirm/",
        PaymentConfirmView.as_view(),
        name="payment-confirm",
    ),
    path(
        "<str:payment_id>/fail/",
        PaymentFailView.as_view(),
        name="payment-fail",
    ),
]
