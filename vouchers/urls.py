from django.urls import path

from vouchers.views import (
    VoucherDetailView,
    VoucherListCreateView,
    VoucherStatusUpdateView,
    VoucherValidateView,
)


urlpatterns = [
    path(
        "",
        VoucherListCreateView.as_view(),
        name="voucher-list-create",
    ),
    path(
        "validate/",
        VoucherValidateView.as_view(),
        name="voucher-validate",
    ),
    path(
        "<str:voucher_id>/status/",
        VoucherStatusUpdateView.as_view(),
        name="voucher-status-update",
    ),
    path(
        "<str:voucher_id>/",
        VoucherDetailView.as_view(),
        name="voucher-detail",
    ),
]
