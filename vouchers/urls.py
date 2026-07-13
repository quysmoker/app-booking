from django.urls import path

from vouchers.views import (
    VoucherDetailView,
    VoucherListCreateView,
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
        "<str:voucher_id>/",
        VoucherDetailView.as_view(),
        name="voucher-detail",
    ),
]
