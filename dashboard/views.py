from collections import defaultdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from bookings.documents import Booking
from courts.documents import Court
from dashboard.services import (
    calculate_daily_revenue,
    calculate_monthly_revenue,
    filter_queryset_by_date,
    get_date_range,
    get_numeric_value,
    is_admin_or_staff,
    serialize_document,
)
from orders.documents import Order
from products.documents import Product
from reviews.documents import Review
from users.documents import User


BOOKING_SUCCESS_STATUSES = [
    "confirmed",
    "completed",
    "paid",
]

ORDER_SUCCESS_STATUSES = [
    "confirmed",
    "processing",
    "shipping",
    "delivered",
    "completed",
    "paid",
]


def permission_denied_response():
    return Response(
        {
            "message": "Permission denied",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def get_status_breakdown(queryset):
    breakdown = defaultdict(int)

    for document in queryset:
        document_status = getattr(
            document,
            "status",
            "unknown",
        )

        breakdown[
            str(document_status or "unknown")
        ] += 1

    return dict(breakdown)


def get_booking_revenue(booking):
    return get_numeric_value(
        booking,
        [
            "total_amount",
            "total_price",
            "amount",
            "price",
        ],
    )


def get_order_revenue(order):
    return get_numeric_value(
        order,
        [
            "total_amount",
            "final_amount",
            "amount",
            "total_price",
        ],
    )


class DashboardOverviewView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return permission_denied_response()

        start_date, end_date, error = (
            get_date_range(request)
        )

        if error:
            return Response(
                {
                    "message": error,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = User.objects()
        courts = Court.objects()
        products = Product.objects()

        bookings = filter_queryset_by_date(
            Booking.objects(),
            start_date=start_date,
            end_date=end_date,
        )

        orders = filter_queryset_by_date(
            Order.objects(),
            start_date=start_date,
            end_date=end_date,
        )

        reviews = filter_queryset_by_date(
            Review.objects(is_active=True),
            start_date=start_date,
            end_date=end_date,
        )

        successful_bookings = [
            booking
            for booking in bookings
            if getattr(
                booking,
                "status",
                "",
            ) in BOOKING_SUCCESS_STATUSES
        ]

        successful_orders = [
            order
            for order in orders
            if getattr(
                order,
                "status",
                "",
            ) in ORDER_SUCCESS_STATUSES
        ]

        booking_revenue = sum(
            get_booking_revenue(booking)
            for booking in successful_bookings
        )

        order_revenue = sum(
            get_order_revenue(order)
            for order in successful_orders
        )

        total_revenue = (
            booking_revenue
            + order_revenue
        )

        average_rating = 0

        if reviews.count() > 0:
            total_rating = sum(
                review.rating
                for review in reviews
            )

            average_rating = round(
                total_rating / reviews.count(),
                2,
            )

        return Response(
            {
                "message": (
                    "Get dashboard overview successfully"
                ),
                "data": {
                    "total_users": users.count(),
                    "total_courts": courts.count(),
                    "total_products": products.count(),
                    "total_bookings": bookings.count(),
                    "total_orders": orders.count(),
                    "total_reviews": reviews.count(),
                    "average_rating": average_rating,
                    "booking_revenue": round(
                        booking_revenue,
                        2,
                    ),
                    "order_revenue": round(
                        order_revenue,
                        2,
                    ),
                    "total_revenue": round(
                        total_revenue,
                        2,
                    ),
                    "booking_status_breakdown": (
                        get_status_breakdown(
                            bookings
                        )
                    ),
                    "order_status_breakdown": (
                        get_status_breakdown(
                            orders
                        )
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class DashboardRevenueView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return permission_denied_response()

        start_date, end_date, error = (
            get_date_range(request)
        )

        if error:
            return Response(
                {
                    "message": error,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        group_by = request.query_params.get(
            "group_by",
            "day",
        )

        if group_by not in ["day", "month"]:
            return Response(
                {
                    "message": (
                        "group_by must be day or month"
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bookings = filter_queryset_by_date(
            Booking.objects(
                status__in=BOOKING_SUCCESS_STATUSES
            ),
            start_date=start_date,
            end_date=end_date,
        )

        orders = filter_queryset_by_date(
            Order.objects(
                status__in=ORDER_SUCCESS_STATUSES
            ),
            start_date=start_date,
            end_date=end_date,
        )

        if group_by == "day":
            booking_data = calculate_daily_revenue(
                bookings,
                [
                    "total_amount",
                    "total_price",
                    "amount",
                    "price",
                ],
            )

            order_data = calculate_daily_revenue(
                orders,
                [
                    "total_amount",
                    "final_amount",
                    "amount",
                    "total_price",
                ],
            )
        else:
            booking_data = (
                calculate_monthly_revenue(
                    bookings,
                    [
                        "total_amount",
                        "total_price",
                        "amount",
                        "price",
                    ],
                )
            )

            order_data = (
                calculate_monthly_revenue(
                    orders,
                    [
                        "total_amount",
                        "final_amount",
                        "amount",
                        "total_price",
                    ],
                )
            )

        return Response(
            {
                "message": (
                    "Get revenue report successfully"
                ),
                "data": {
                    "group_by": group_by,
                    "booking_revenue": booking_data,
                    "order_revenue": order_data,
                },
            },
            status=status.HTTP_200_OK,
        )


class DashboardBookingReportView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return permission_denied_response()

        start_date, end_date, error = (
            get_date_range(request)
        )

        if error:
            return Response(
                {
                    "message": error,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bookings = filter_queryset_by_date(
            Booking.objects(),
            start_date=start_date,
            end_date=end_date,
        )

        total_bookings = bookings.count()

        successful_count = 0
        cancelled_count = 0
        pending_count = 0
        total_revenue = 0

        court_statistics = defaultdict(
            lambda: {
                "court_id": "",
                "court_name": "",
                "booking_count": 0,
                "revenue": 0,
            }
        )

        for booking in bookings:
            booking_status = getattr(
                booking,
                "status",
                "",
            )

            if booking_status in BOOKING_SUCCESS_STATUSES:
                successful_count += 1
                total_revenue += (
                    get_booking_revenue(booking)
                )

            elif booking_status in [
                "cancelled",
                "canceled",
                "rejected",
            ]:
                cancelled_count += 1

            else:
                pending_count += 1

            court = getattr(
                booking,
                "court",
                None,
            )

            court_id = ""

            if court:
                court_id = str(
                    getattr(
                        court,
                        "id",
                        court,
                    )
                )

            if not court_id:
                court_id = str(
                    getattr(
                        booking,
                        "court_id",
                        "unknown",
                    )
                )

            court_name = getattr(
                court,
                "name",
                "",
            )

            if not court_name:
                court_name = getattr(
                    booking,
                    "court_name",
                    "",
                )

            court_statistics[
                court_id
            ]["court_id"] = court_id

            court_statistics[
                court_id
            ]["court_name"] = court_name

            court_statistics[
                court_id
            ]["booking_count"] += 1

            if booking_status in BOOKING_SUCCESS_STATUSES:
                court_statistics[
                    court_id
                ]["revenue"] += (
                    get_booking_revenue(booking)
                )

        top_courts = sorted(
            court_statistics.values(),
            key=lambda item: item["booking_count"],
            reverse=True,
        )

        for court in top_courts:
            court["revenue"] = round(
                court["revenue"],
                2,
            )

        success_rate = 0

        if total_bookings > 0:
            success_rate = round(
                successful_count
                / total_bookings
                * 100,
                2,
            )

        return Response(
            {
                "message": (
                    "Get booking report successfully"
                ),
                "data": {
                    "total_bookings": total_bookings,
                    "successful_count": (
                        successful_count
                    ),
                    "cancelled_count": (
                        cancelled_count
                    ),
                    "pending_count": pending_count,
                    "success_rate": success_rate,
                    "total_revenue": round(
                        total_revenue,
                        2,
                    ),
                    "status_breakdown": (
                        get_status_breakdown(
                            bookings
                        )
                    ),
                    "top_courts": top_courts[:10],
                },
            },
            status=status.HTTP_200_OK,
        )


class DashboardOrderReportView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return permission_denied_response()

        start_date, end_date, error = (
            get_date_range(request)
        )

        if error:
            return Response(
                {
                    "message": error,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        orders = filter_queryset_by_date(
            Order.objects(),
            start_date=start_date,
            end_date=end_date,
        )

        total_orders = orders.count()
        successful_count = 0
        cancelled_count = 0
        pending_count = 0
        total_revenue = 0
        total_discount = 0

        product_statistics = defaultdict(
            lambda: {
                "product_id": "",
                "product_name": "",
                "quantity_sold": 0,
                "revenue": 0,
            }
        )

        for order in orders:
            order_status = getattr(
                order,
                "status",
                "",
            )

            if order_status in ORDER_SUCCESS_STATUSES:
                successful_count += 1
                total_revenue += (
                    get_order_revenue(order)
                )

            elif order_status in [
                "cancelled",
                "canceled",
                "rejected",
            ]:
                cancelled_count += 1

            else:
                pending_count += 1

            total_discount += get_numeric_value(
                order,
                [
                    "discount_amount",
                    "discount",
                ],
            )

            items = getattr(
                order,
                "items",
                [],
            ) or []

            for item in items:
                product_id = str(
                    getattr(
                        item,
                        "product_id",
                        "",
                    )
                )

                product_name = getattr(
                    item,
                    "product_name",
                    "",
                )

                if not product_name:
                    product_name = getattr(
                        item,
                        "name",
                        "",
                    )

                quantity = int(
                    getattr(
                        item,
                        "quantity",
                        0,
                    )
                    or 0
                )

                item_price = get_numeric_value(
                    item,
                    [
                        "price",
                        "unit_price",
                        "product_price",
                    ],
                )

                product_statistics[
                    product_id
                ]["product_id"] = product_id

                product_statistics[
                    product_id
                ]["product_name"] = (
                    product_name
                )

                product_statistics[
                    product_id
                ]["quantity_sold"] += quantity

                if order_status in ORDER_SUCCESS_STATUSES:
                    product_statistics[
                        product_id
                    ]["revenue"] += (
                        item_price * quantity
                    )

        top_products = sorted(
            product_statistics.values(),
            key=lambda item: item["quantity_sold"],
            reverse=True,
        )

        for product in top_products:
            product["revenue"] = round(
                product["revenue"],
                2,
            )

        success_rate = 0

        if total_orders > 0:
            success_rate = round(
                successful_count
                / total_orders
                * 100,
                2,
            )

        return Response(
            {
                "message": (
                    "Get order report successfully"
                ),
                "data": {
                    "total_orders": total_orders,
                    "successful_count": (
                        successful_count
                    ),
                    "cancelled_count": (
                        cancelled_count
                    ),
                    "pending_count": pending_count,
                    "success_rate": success_rate,
                    "total_revenue": round(
                        total_revenue,
                        2,
                    ),
                    "total_discount": round(
                        total_discount,
                        2,
                    ),
                    "status_breakdown": (
                        get_status_breakdown(
                            orders
                        )
                    ),
                    "top_products": (
                        top_products[:10]
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class DashboardRecentActivityView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return permission_denied_response()

        try:
            limit = int(
                request.query_params.get(
                    "limit",
                    10,
                )
            )
        except (TypeError, ValueError):
            return Response(
                {
                    "message": (
                        "limit must be an integer"
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit < 1:
            limit = 10

        if limit > 50:
            limit = 50

        recent_bookings = (
            Booking.objects()
            .order_by("-created_at")
            .limit(limit)
        )

        recent_orders = (
            Order.objects()
            .order_by("-created_at")
            .limit(limit)
        )

        recent_reviews = (
            Review.objects(is_active=True)
            .order_by("-created_at")
            .limit(limit)
        )

        return Response(
            {
                "message": (
                    "Get recent activity successfully"
                ),
                "data": {
                    "bookings": [
                        serialize_document(booking)
                        for booking
                        in recent_bookings
                    ],
                    "orders": [
                        serialize_document(order)
                        for order
                        in recent_orders
                    ],
                    "reviews": [
                        serialize_document(review)
                        for review
                        in recent_reviews
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )
