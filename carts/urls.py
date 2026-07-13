from django.urls import path

from carts.views import (
    CartAddItemView,
    CartClearView,
    CartDetailView,
    CartItemDetailView,
)


urlpatterns = [
    path(
        "",
        CartDetailView.as_view(),
        name="cart-detail",
    ),
    path(
        "items/",
        CartAddItemView.as_view(),
        name="cart-add-item",
    ),
    path(
        "items/<str:product_id>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path(
        "clear/",
        CartClearView.as_view(),
        name="cart-clear",
    ),
]
