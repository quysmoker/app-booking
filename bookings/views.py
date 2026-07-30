
from datetime import datetime, timezone

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import (
    login_required,
    role_required,
)
from bookings.documents import Booking
from courts.documents import Court
from notifications.services import create_notification


def parse_datetime(value, booking_date=None):
    if not value:
        return None

    value = str(value).strip()

    # Hỗ trợ dữ liệu:
    # booking_date: 2026-08-01
    # start_time: 08:00
    if (
        booking_date
        and ":" in value
        and "T" not in value
    ):
        value = f"{booking_date}T{value}"

    # Chuyển ký hiệu Z sang timezone UTC.
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"

    try:
        parsed_value = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

    # MongoDB đang lưu datetime không kèm timezone.
    if parsed_value.tzinfo is not None:
        parsed_value = (
            parsed_value
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )

    return parsed_value


def get_booking_times(data, current_booking=None):
    booking_date = data.get("booking_date")

    if data.get("start_time") is not None:
        start_time = parse_datetime(
            data.get("start_time"),
            booking_date,
        )
    else:
        start_time = getattr(
            current_booking,
            "start_time",
            None,
        )

    if data.get("end_time") is not None:
        end_time = parse_datetime(
            data.get("end_time"),
            booking_date,
        )
    else:
        end_time = getattr(
            current_booking,
            "end_time",
            None,
        )

    return start_time, end_time


def get_booking_by_id(booking_id):
    try:
        return Booking.objects(
            id=ObjectId(booking_id)
        ).first()
    except Exception:
        return None


def has_time_conflict(
    court,
    start_time,
    end_time,
    exclude_booking_id=None,
):
    """
    Hai lịch bị trùng khi:
    lịch cũ bắt đầu trước lúc lịch mới kết thúc
    và lịch cũ kết thúc sau lúc lịch mới bắt đầu.
    """
    bookings = Booking.objects(
        court=court,
        status__in=[
            "pending",
            "confirmed",
        ],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )

    if exclude_booking_id:
        try:
            bookings = bookings.filter(
                id__ne=ObjectId(exclude_booking_id)
            )
        except Exception:
            return True

    return bookings.first() is not None


def send_booking_status_notification(booking):
    status_labels = {
        "confirmed": "đã được xác nhận",
        "completed": "đã hoàn thành",
        "cancelled": "đã bị hủy",
    }

    create_notification(
        recipient=booking.user,
        notification_type="booking",
        title="Cập nhật trạng thái đặt sân",
        message=(
            f"Yêu cầu đặt sân của bạn "
            f"{status_labels.get(
                booking.status,
                'đã được cập nhật',
            )}."
        ),
        related_id=str(booking.id),
        related_type="booking",
        data={
            "booking_id": str(booking.id),
            "status": booking.status,
        },
    )


class BookingListCreateView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if user.role in ["admin", "staff"]:
            bookings = Booking.objects()
        else:
            bookings = Booking.objects(user=user)

        booking_status = request.query_params.get(
            "status"
        )

        if booking_status:
            if booking_status not in Booking.STATUS_CHOICES:
                return Response(
                    {
                        "message": (
                            "Invalid booking status"
                        ),
                        "allowed_statuses": list(
                            Booking.STATUS_CHOICES
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            bookings = bookings.filter(
                status=booking_status
            )

        return Response(
            {
                "message": "Get bookings successfully",
                "data": [
                    booking.to_json_data()
                    for booking in bookings
                ],
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        court_id = data.get("court_id")

        start_time, end_time = get_booking_times(
            data
        )

        note = str(
            data.get("note", "")
        ).strip()

        if (
            not court_id
            or not start_time
            or not end_time
        ):
            return Response(
                {
                    "message": (
                        "court_id, start_time and "
                        "end_time are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_time >= end_time:
            return Response(
                {
                    "message": (
                        "start_time must be before "
                        "end_time"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_time <= datetime.utcnow():
            return Response(
                {
                    "message": (
                        "start_time must be in the future"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            court = Court.objects(
                id=ObjectId(court_id),
                is_active=True,
                status="available",
            ).first()
        except Exception:
            court = None

        if not court:
            return Response(
                {
                    "message": (
                        "Court not found or unavailable"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if has_time_conflict(
            court,
            start_time,
            end_time,
        ):
            return Response(
                {
                    "message": (
                        "Court is already booked in "
                        "this time range"
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        hours = (
            end_time - start_time
        ).total_seconds() / 3600

        total_price = (
            hours * court.price_per_hour
        )

        booking = Booking(
            user=user,
            court=court,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            status="pending",
            note=note,
        )
        booking.save()

        create_notification(
            recipient=user,
            notification_type="booking",
            title="Đặt sân thành công",
            message=(
                "Yêu cầu đặt sân của bạn đã được tạo "
                "và đang chờ xác nhận."
            ),
            related_id=str(booking.id),
            related_type="booking",
            data={
                "booking_id": str(booking.id),
                "status": booking.status,
            },
        )

        return Response(
            {
                "message": "Create booking successfully",
                "data": booking.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class BookingDetailView(APIView):
    @login_required
    def get(self, request, booking_id):
        booking = get_booking_by_id(booking_id)

        if not booking:
            return Response(
                {"message": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and booking.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": (
                    "Get booking detail successfully"
                ),
                "data": booking.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def put(self, request, booking_id):
        booking = get_booking_by_id(booking_id)

        if not booking:
            return Response(
                {"message": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and booking.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.role == "user"
            and booking.status != "pending"
        ):
            return Response(
                {
                    "message": (
                        "Only pending bookings can be edited"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trạng thái phải được đổi bằng API riêng.
        if request.data.get("status") is not None:
            return Response(
                {
                    "message": (
                        "Use the booking status endpoint "
                        "to change status"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time, end_time = get_booking_times(
            request.data,
            current_booking=booking,
        )

        if not start_time or not end_time:
            return Response(
                {
                    "message": (
                        "start_time and end_time must be "
                        "valid ISO datetimes"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_time >= end_time:
            return Response(
                {
                    "message": (
                        "start_time must be before end_time"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_time <= datetime.utcnow():
            return Response(
                {
                    "message": (
                        "start_time must be in the future"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if has_time_conflict(
            booking.court,
            start_time,
            end_time,
            exclude_booking_id=booking_id,
        ):
            return Response(
                {
                    "message": (
                        "Court is already booked in "
                        "this time range"
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        hours = (
            end_time - start_time
        ).total_seconds() / 3600

        booking.start_time = start_time
        booking.end_time = end_time
        booking.total_price = (
            hours * booking.court.price_per_hour
        )

        if request.data.get("note") is not None:
            booking.note = str(
                request.data.get("note")
            ).strip()

        booking.updated_at = datetime.utcnow()
        booking.save()

        return Response(
            {
                "message": "Update booking successfully",
                "data": booking.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def delete(self, request, booking_id):
        booking = get_booking_by_id(booking_id)

        if not booking:
            return Response(
                {"message": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and booking.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status not in [
            "pending",
            "confirmed",
        ]:
            return Response(
                {
                    "message": (
                        "Only pending or confirmed "
                        "bookings can be cancelled"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            user.role == "user"
            and booking.status != "pending"
        ):
            return Response(
                {
                    "message": (
                        "Users can only cancel "
                        "pending bookings"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Xóa lịch đặt được xử lý thành hủy lịch,
        # không xóa dữ liệu khỏi MongoDB.
        booking.status = "cancelled"
        booking.updated_at = datetime.utcnow()
        booking.save()

        send_booking_status_notification(booking)

        return Response(
            {
                "message": "Cancel booking successfully",
                "data": booking.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class BookingStatusUpdateView(APIView):
    @role_required(["admin", "staff"])
    def patch(self, request, booking_id):
        booking = get_booking_by_id(booking_id)

        if not booking:
            return Response(
                {"message": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")

        transitions = {
            "pending": [
                "confirmed",
                "cancelled",
            ],
            "confirmed": [
                "completed",
                "cancelled",
            ],
            "completed": [],
            "cancelled": [],
        }

        allowed_statuses = transitions.get(
            booking.status,
            [],
        )

        if new_status not in allowed_statuses:
            return Response(
                {
                    "message": (
                        "Invalid status transition"
                    ),
                    "current_status": booking.status,
                    "allowed_statuses": (
                        allowed_statuses
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = new_status
        booking.updated_at = datetime.utcnow()
        booking.save()

        send_booking_status_notification(booking)

        return Response(
            {
                "message": (
                    "Update booking status successfully"
                ),
                "data": booking.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
