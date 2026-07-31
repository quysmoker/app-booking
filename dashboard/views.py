import calendar
from collections import defaultdict
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import role_required
from bookings.documents import Booking
from courts.documents import Court
from dashboard.services import (
    filter_queryset_by_date,
    get_date_range,
)
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


class DashboardReportView(APIView):
    @role_required(["admin", "staff"])
    def get(self, request):
        start_date, end_date, date_error = (
            get_date_range(request)
        )

        if date_error:
            return Response(
                {"message": date_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bookings = filter_queryset_by_date(
            Booking.objects(),
            start_date=start_date,
            end_date=end_date,
            field_name="created_at",
        )

        orders = filter_queryset_by_date(
            Order.objects(),
            start_date=start_date,
            end_date=end_date,
            field_name="created_at",
        )

        completed_bookings = list(
            bookings.filter(status="completed")
        )
        completed_orders = list(
            orders.filter(status="completed")
        )

        booking_revenue = sum(
            float(booking.total_price or 0)
            for booking in completed_bookings
        )
        order_revenue = sum(
            float(order.total_amount or 0)
            for order in completed_orders
        )

        booking_statuses = {
            item: bookings.filter(status=item).count()
            for item in Booking.STATUS_CHOICES
        }
        order_statuses = {
            item: orders.filter(status=item).count()
            for item in Order.STATUS_CHOICES
        }

        daily_data = defaultdict(
            lambda: {
                "booking_revenue": 0.0,
                "order_revenue": 0.0,
            }
        )

        for booking in completed_bookings:
            if not booking.created_at:
                continue

            date_key = booking.created_at.strftime(
                "%Y-%m-%d"
            )
            daily_data[date_key][
                "booking_revenue"
            ] += float(booking.total_price or 0)

        for order in completed_orders:
            if not order.created_at:
                continue

            date_key = order.created_at.strftime(
                "%Y-%m-%d"
            )
            daily_data[date_key][
                "order_revenue"
            ] += float(order.total_amount or 0)

        daily_revenue = []

        for date_key in sorted(daily_data):
            booking_amount = daily_data[
                date_key
            ]["booking_revenue"]
            order_amount = daily_data[
                date_key
            ]["order_revenue"]

            daily_revenue.append(
                {
                    "date": date_key,
                    "booking_revenue": round(
                        booking_amount,
                        2,
                    ),
                    "order_revenue": round(
                        order_amount,
                        2,
                    ),
                    "total_revenue": round(
                        booking_amount + order_amount,
                        2,
                    ),
                }
            )

        court_statistics = {}

        for booking in completed_bookings:
            court = booking.court

            if not court:
                continue

            court_id = str(court.id)

            if court_id not in court_statistics:
                court_statistics[court_id] = {
                    "court_id": court_id,
                    "court_name": court.name,
                    "sport_type": court.sport_type,
                    "booking_count": 0,
                    "revenue": 0.0,
                }

            court_statistics[court_id][
                "booking_count"
            ] += 1
            court_statistics[court_id][
                "revenue"
            ] += float(booking.total_price or 0)

        top_courts = sorted(
            court_statistics.values(),
            key=lambda item: (
                item["revenue"],
                item["booking_count"],
            ),
            reverse=True,
        )[:5]

        for item in top_courts:
            item["revenue"] = round(
                item["revenue"],
                2,
            )

        product_statistics = {}

        for order in completed_orders:
            for item in order.items:
                product_id = str(item.product_id)

                if product_id not in product_statistics:
                    product_statistics[product_id] = {
                        "product_id": product_id,
                        "product_name": item.product_name,
                        "quantity": 0,
                        "revenue": 0.0,
                    }

                product_statistics[product_id][
                    "quantity"
                ] += int(item.quantity or 0)
                product_statistics[product_id][
                    "revenue"
                ] += float(item.subtotal or 0)

        top_products = sorted(
            product_statistics.values(),
            key=lambda item: (
                item["quantity"],
                item["revenue"],
            ),
            reverse=True,
        )[:5]

        for item in top_products:
            item["revenue"] = round(
                item["revenue"],
                2,
            )

        data = {
            "period": {
                "start_date": request.query_params.get(
                    "start_date"
                ),
                "end_date": request.query_params.get(
                    "end_date"
                ),
            },
            "summary": {
                "total_revenue": round(
                    booking_revenue + order_revenue,
                    2,
                ),
                "booking_revenue": round(
                    booking_revenue,
                    2,
                ),
                "order_revenue": round(
                    order_revenue,
                    2,
                ),
                "total_bookings": bookings.count(),
                "completed_bookings": len(
                    completed_bookings
                ),
                "total_orders": orders.count(),
                "completed_orders": len(
                    completed_orders
                ),
            },
            "booking_statuses": booking_statuses,
            "order_statuses": order_statuses,
            "daily_revenue": daily_revenue,
            "top_courts": top_courts,
            "top_products": top_products,
        }

        return Response(
            {
                "message": (
                    "Get dashboard report successfully"
                ),
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
