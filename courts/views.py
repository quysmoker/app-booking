from bson import ObjectId
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from courts.documents import Court
from authentication.permissions import role_required


class CourtListCreateView(APIView):
    def get(self, request):
        courts = Court.objects(is_active=True)

        return Response({
            "message": "Get courts successfully",
            "data": [court.to_json_data() for court in courts]
        }, status=status.HTTP_200_OK)

    @role_required(["admin", "staff"])
    def post(self, request):
        data = request.data

        name = data.get("name")
        location = data.get("location")
        price_per_hour = data.get("price_per_hour")

        if not name or not location or price_per_hour is None:
            return Response({
                "message": "name, location and price_per_hour are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        court = Court(
            name=name,
            description=data.get("description", ""),
            location=location,
            image=data.get("image", ""),
            price_per_hour=float(price_per_hour),
        )
        court.save()

        return Response({
            "message": "Create court successfully",
            "data": court.to_json_data()
        }, status=status.HTTP_201_CREATED)


class CourtDetailView(APIView):
    def get_court(self, court_id):
        try:
            return Court.objects(id=ObjectId(court_id)).first()
        except Exception:
            return None

    def get(self, request, court_id):
        court = self.get_court(court_id)

        if not court:
            return Response({"message": "Court not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "Get court detail successfully",
            "data": court.to_json_data()
        }, status=status.HTTP_200_OK)

    @role_required(["admin", "staff"])
    def put(self, request, court_id):
        court = self.get_court(court_id)

        if not court:
            return Response({"message": "Court not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        court.name = data.get("name", court.name)
        court.description = data.get("description", court.description)
        court.location = data.get("location", court.location)
        court.image = data.get("image", court.image)

        if data.get("price_per_hour") is not None:
            court.price_per_hour = float(data.get("price_per_hour"))

        if data.get("is_active") is not None:
            court.is_active = bool(data.get("is_active"))

        court.updated_at = datetime.utcnow()
        court.save()

        return Response({
            "message": "Update court successfully",
            "data": court.to_json_data()
        }, status=status.HTTP_200_OK)

    @role_required(["admin", "staff"])
    def delete(self, request, court_id):
        court = self.get_court(court_id)

        if not court:
            return Response({"message": "Court not found"}, status=status.HTTP_404_NOT_FOUND)

        court.is_active = False
        court.updated_at = datetime.utcnow()
        court.save()

        return Response({
            "message": "Delete court successfully"
        }, status=status.HTTP_200_OK)
