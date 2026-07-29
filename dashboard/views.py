
import calendar
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import role_required
from bookings.documents import Booking
from courts.documents import Court
from orders.documents import Order
from products.documents import Product
from users.documents import User


def get_day_range():
    now = datetime.utcnow()

    start_of_day = datetime(
        now.year,
        now.month,
        now.day,
    )

    end_of_day = start_of_day + timedelta(days=1)

    return start_of_day, end_of_day


def get_month_range(year, month):
    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    return start_date, end_date


def get_recent_months(number_of_months=6):
    now = datetime.utcnow()
    months = []

    year = now.year
    month = now.month

    for _ in range(number_of_months):
        months.append((year, month))

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    months.reverse()

    return months


def safe_booking_data(booking):
    try:
        return booking.to_json_data()
    except Exception:
        return {
            "id": str(booking.id),
            "user": None,
            "court": None,
            "start_time": (
                booking.start_time.isoformat()
                if booking.start_time
                else None
            ),
            "end_time": (
                booking.end_time.isoformat()
                if booking.end_time
                else None
            ),
            "total_price": booking.total_price,
            "status": booking.status,
            "note": booking.note,
            "created_at": (
                booking.created_at.isoformat()
                if booking.created_at
                else None
            ),
        }


def safe_order_data(order):
    try:
        return order.to_json_data()
    except Exception:
        return {
            "id": str(order.id),
            "code": order.code,
            "user": None,
            "items": [
                item.to_json_data()
                for item in order.items
            ],
            "recipient_name": order.recipient_name,
            "recipient_phone": order.recipient_phone,
            "shipping_address": order.shipping_address,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "created_at": (
                order.created_at.isoformat()
                if order.created_at
                else None
            ),
        }


class DashboardOverviewView(APIView):
    @role_required(["admin", "staff"])
    def get(self, request):
        start_of_day, end_of_day = get_day_range()

        completed_bookings = Booking.objects(
            status="completed"
        )

        completed_orders = Order.objects(
            status="completed"
        )

        booking_revenue = sum(
            booking.total_price or 0
            for booking in completed_bookings
        )

        order_revenue = sum(
            order.total_amount or 0
            for order in completed_orders
        )

        total_revenue = booking_revenue + order_revenue

        total_bookings = Booking.objects.count()
        total_orders = Order.objects.count()

        total_customers = User.objects(
            role="user"
        ).count()

        total_courts = Court.objects.count()
        active_courts = Court.objects(
            is_active=True
        ).count()

        total_products = Product.objects.count()
        active_products = Product.objects(
            is_active=True
        ).count()

        bookings_today = Booking.objects(
            start_time__gte=start_of_day,
            start_time__lt=end_of_day,
        ).count()

        orders_today = Order.objects(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
        ).count()

        pending_bookings = Booking.objects(
            status="pending"
        ).count()

        pending_orders = Order.objects(
            status="pending"
        ).count()

        monthly_statistics = []

        for year, month in get_recent_months(6):
            month_start, month_end = get_month_range(
                year,
                month,
            )

            month_bookings = Booking.objects(
                created_at__gte=month_start,
                created_at__lt=month_end,
            )

            completed_month_bookings = (
                month_bookings.filter(
                    status="completed"
                )
            )

            month_orders = Order.objects(
                created_at__gte=month_start,
                created_at__lt=month_end,
            )

            completed_month_orders = (
                month_orders.filter(
                    status="completed"
                )
            )

            monthly_booking_revenue = sum(
                booking.total_price or 0
                for booking in completed_month_bookings
            )

            monthly_order_revenue = sum(
                order.total_amount or 0
                for order in completed_month_orders
            )

            monthly_statistics.append(
                {
                    "year": year,
                    "month": month,
                    "label": (
                        f"Tháng {month}"
                    ),
                    "short_label": (
                        f"{month:02d}/{year}"
                    ),
                    "booking_count": (
                        month_bookings.count()
                    ),
                    "order_count": (
                        month_orders.count()
                    ),
                    "booking_revenue": (
                        monthly_booking_revenue
                    ),
                    "order_revenue": (
                        monthly_order_revenue
                    ),
                    "total_revenue": (
                        monthly_booking_revenue
                        + monthly_order_revenue
                    ),
                }
            )

        recent_bookings = Booking.objects()[:5]
        recent_orders = Order.objects()[:5]

        data = {
            "summary": {
                "total_revenue": total_revenue,
                "booking_revenue": booking_revenue,
                "order_revenue": order_revenue,
                "total_bookings": total_bookings,
                "total_orders": total_orders,
                "total_customers": total_customers,
                "total_courts": total_courts,
                "active_courts": active_courts,
                "total_products": total_products,
                "active_products": active_products,
                "bookings_today": bookings_today,
                "orders_today": orders_today,
                "pending_bookings": pending_bookings,
                "pending_orders": pending_orders,
            },
            "monthly_statistics": monthly_statistics,
            "recent_bookings": [
                safe_booking_data(booking)
                for booking in recent_bookings
            ],
            "recent_orders": [
                safe_order_data(order)
                for order in recent_orders
            ],
        }

        return Response(
            {
                "message": (
                    "Get dashboard statistics successfully"
                ),
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
