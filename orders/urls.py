from django.urls import path

from orders.views import (
    OrderCancelView,
    OrderDetailView,
    OrderListCreateView,
    OrderStatusUpdateView,
)


urlpatterns = [
    path(
        "",
        OrderListCreateView.as_view(),
        name="order-list-create",
    ),
    path(
        "<str:order_id>/",
        OrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "<str:order_id>/status/",
        OrderStatusUpdateView.as_view(),
        name="order-status-update",
    ),
    path(
        "<str:order_id>/cancel/",
        OrderCancelView.as_view(),
        name="order-cancel",
    ),
]
