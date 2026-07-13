from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view



@api_view(["GET"])
def health_check(request):
    return Response({
        "message": "Sport Booking API is running",
        "status": "success"
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/auth/", include("authentication.urls")),
    path("api/courts/", include("courts.urls")),
    path("api/bookings/", include("bookings.urls")),
    path("api/products/", include("products.urls")),
    path("api/cart/", include("carts.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/vouchers/", include("vouchers.urls")),
]
