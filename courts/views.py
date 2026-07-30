

from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import role_required
from courts.documents import Court


def get_court_by_id(court_id):
    try:
        return Court.objects(
            id=ObjectId(court_id)
        ).first()
    except Exception:
        return None


def parse_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None

    if price < 0:
        return None

    return price


class CourtListCreateView(APIView):
    def get(self, request):
        courts = Court.objects(is_active=True)

        sport_type = request.query_params.get(
            "sport_type"
        )
        court_status = request.query_params.get(
            "status"
        )

        if sport_type:
            if sport_type not in Court.SPORT_TYPE_CHOICES:
                return Response(
                    {
                        "message": "Invalid sport_type",
                        "allowed_sport_types": list(
                            Court.SPORT_TYPE_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            courts = courts.filter(
                sport_type=sport_type
            )

        if court_status:
            if court_status not in Court.STATUS_CHOICES:
                return Response(
                    {
                        "message": "Invalid court status",
                        "allowed_statuses": list(
                            Court.STATUS_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            courts = courts.filter(
                status=court_status
            )

        return Response(
            {
                "message": "Get courts successfully",
                "data": [
                    court.to_json_data()
                    for court in courts
                ],
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def post(self, request):
        data = request.data

        name = str(
            data.get("name", "")
        ).strip()

        # Hỗ trợ cả location mới và address cũ.
        location = str(
            data.get("location")
            or data.get("address")
            or ""
        ).strip()

        sport_type = data.get(
            "sport_type",
            "pickleball",
        )

        court_status = data.get(
            "status",
            "available",
        )

        price_per_hour = parse_price(
            data.get("price_per_hour")
        )

        if not name or not location:
            return Response(
                {
                    "message": (
                        "name and location are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if price_per_hour is None:
            return Response(
                {
                    "message": (
                        "price_per_hour must be a valid "
                        "non-negative number"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sport_type not in Court.SPORT_TYPE_CHOICES:
            return Response(
                {
                    "message": "Invalid sport_type",
                    "allowed_sport_types": list(
                        Court.SPORT_TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if court_status not in Court.STATUS_CHOICES:
            return Response(
                {
                    "message": "Invalid court status",
                    "allowed_statuses": list(
                        Court.STATUS_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        court = Court(
            name=name,
            description=str(
                data.get("description", "")
            ).strip(),
            sport_type=sport_type,
            location=location,
            image=str(
                data.get("image", "")
            ).strip(),
            price_per_hour=price_per_hour,
            status=court_status,
            is_active=True,
        )

        court.save()

        return Response(
            {
                "message": "Create court successfully",
                "data": court.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class CourtDetailView(APIView):
    def get(self, request, court_id):
        court = get_court_by_id(court_id)

        if not court or not court.is_active:
            return Response(
                {"message": "Court not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": (
                    "Get court detail successfully"
                ),
                "data": court.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def put(self, request, court_id):
        court = get_court_by_id(court_id)

        if not court:
            return Response(
                {"message": "Court not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data

        if data.get("name") is not None:
            name = str(
                data.get("name")
            ).strip()

            if not name:
                return Response(
                    {
                        "message": (
                            "name cannot be empty"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            court.name = name

        location_value = data.get("location")

        if location_value is None:
            location_value = data.get("address")

        if location_value is not None:
            location = str(
                location_value
            ).strip()

            if not location:
                return Response(
                    {
                        "message": (
                            "location cannot be empty"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            court.location = location

        if data.get("sport_type") is not None:
            sport_type = data.get("sport_type")

            if sport_type not in Court.SPORT_TYPE_CHOICES:
                return Response(
                    {
                        "message": "Invalid sport_type",
                        "allowed_sport_types": list(
                            Court.SPORT_TYPE_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            court.sport_type = sport_type

        if data.get("status") is not None:
            court_status = data.get("status")

            if court_status not in Court.STATUS_CHOICES:
                return Response(
                    {
                        "message": "Invalid court status",
                        "allowed_statuses": list(
                            Court.STATUS_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            court.status = court_status

        if data.get("price_per_hour") is not None:
            price = parse_price(
                data.get("price_per_hour")
            )

            if price is None:
                return Response(
                    {
                        "message": (
                            "price_per_hour must be a valid "
                            "non-negative number"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            court.price_per_hour = price

        if data.get("description") is not None:
            court.description = str(
                data.get("description")
            ).strip()

        if data.get("image") is not None:
            court.image = str(
                data.get("image")
            ).strip()

        court.updated_at = datetime.utcnow()
        court.save()

        return Response(
            {
                "message": "Update court successfully",
                "data": court.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def delete(self, request, court_id):
        court = get_court_by_id(court_id)

        if not court:
            return Response(
                {"message": "Court not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Xóa mềm để không làm mất dữ liệu lịch đặt.
        court.is_active = False
        court.status = "unavailable"
        court.updated_at = datetime.utcnow()
        court.save()

        return Response(
            {"message": "Delete court successfully"},
            status=status.HTTP_200_OK,
        )
