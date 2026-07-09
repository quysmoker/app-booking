from bson import ObjectId
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from bookings.documents import Booking
from courts.documents import Court
from authentication.permissions import login_required


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def has_time_conflict(court, start_time, end_time, exclude_booking_id=None):
    query = {
        "court": court,
        "status__in": ["pending", "confirmed"],
        "start_time__lt": end_time,
        "end_time__gt": start_time,
    }

    bookings = Booking.objects(**query)

    if exclude_booking_id:
        bookings = bookings.filter(id__ne=ObjectId(exclude_booking_id))

    return bookings.first() is not None


class BookingListCreateView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if user.role in ["admin", "staff"]:
            bookings = Booking.objects()
        else:
            bookings = Booking.objects(user=user)

        return Response({
            "message": "Get bookings successfully",
            "data": [booking.to_json_data() for booking in bookings]
        }, status=status.HTTP_200_OK)

    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        court_id = data.get("court_id")
        start_time = parse_datetime(data.get("start_time"))
        end_time = parse_datetime(data.get("end_time"))
        note = data.get("note", "")

        if not court_id or not start_time or not end_time:
            return Response({
                "message": "court_id, start_time and end_time are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if start_time >= end_time:
            return Response({
                "message": "start_time must be before end_time"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            court = Court.objects(id=ObjectId(court_id), is_active=True).first()
        except Exception:
            court = None

        if not court:
            return Response({
                "message": "Court not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if has_time_conflict(court, start_time, end_time):
            return Response({
                "message": "Court is already booked in this time range"
            }, status=status.HTTP_400_BAD_REQUEST)

        hours = (end_time - start_time).total_seconds() / 3600
        total_price = hours * court.price_per_hour

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

        return Response({
            "message": "Create booking successfully",
            "data": booking.to_json_data()
        }, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    def get_booking(self, booking_id):
        try:
            return Booking.objects(id=ObjectId(booking_id)).first()
        except Exception:
            return None

    @login_required
    def get(self, request, booking_id):
        booking = self.get_booking(booking_id)

        if not booking:
            return Response({
                "message": "Booking not found"
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.current_user

        if user.role not in ["admin", "staff"] and booking.user.id != user.id:
            return Response({
                "message": "Permission denied"
            }, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "message": "Get booking detail successfully",
            "data": booking.to_json_data()
        }, status=status.HTTP_200_OK)

    @login_required
    def put(self, request, booking_id):
        booking = self.get_booking(booking_id)

        if not booking:
            return Response({
                "message": "Booking not found"
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.current_user
        data = request.data

        if user.role not in ["admin", "staff"] and booking.user.id != user.id:
            return Response({
                "message": "Permission denied"
            }, status=status.HTTP_403_FORBIDDEN)

        new_start_time = parse_datetime(data.get("start_time")) if data.get("start_time") else booking.start_time
        new_end_time = parse_datetime(data.get("end_time")) if data.get("end_time") else booking.end_time

        if new_start_time >= new_end_time:
            return Response({
                "message": "start_time must be before end_time"
            }, status=status.HTTP_400_BAD_REQUEST)

        if has_time_conflict(booking.court, new_start_time, new_end_time, exclude_booking_id=booking_id):
            return Response({
                "message": "Court is already booked in this time range"
            }, status=status.HTTP_400_BAD_REQUEST)

        booking.start_time = new_start_time
        booking.end_time = new_end_time

        hours = (booking.end_time - booking.start_time).total_seconds() / 3600
        booking.total_price = hours * booking.court.price_per_hour

        if data.get("note") is not None:
            booking.note = data.get("note")

        if data.get("status") is not None:
            if user.role not in ["admin", "staff"]:
                return Response({
                    "message": "Only admin or staff can update booking status"
                }, status=status.HTTP_403_FORBIDDEN)

            if data.get("status") not in ["pending", "confirmed", "cancelled", "completed"]:
                return Response({
                    "message": "Invalid booking status"
                }, status=status.HTTP_400_BAD_REQUEST)

            booking.status = data.get("status")

        booking.updated_at = datetime.utcnow()
        booking.save()

        return Response({
            "message": "Update booking successfully",
            "data": booking.to_json_data()
        }, status=status.HTTP_200_OK)

    @login_required
    def delete(self, request, booking_id):
        booking = self.get_booking(booking_id)

        if not booking:
            return Response({
                "message": "Booking not found"
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.current_user

        if user.role not in ["admin", "staff"] and booking.user.id != user.id:
            return Response({
                "message": "Permission denied"
            }, status=status.HTTP_403_FORBIDDEN)

        booking.status = "cancelled"
        booking.updated_at = datetime.utcnow()
        booking.save()

        return Response({
            "message": "Cancel booking successfully"
        }, status=status.HTTP_200_OK)
