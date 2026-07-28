from datetime import datetime

from bson import ObjectId
from mongoengine.errors import NotUniqueError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from bookings.documents import Booking
from courts.documents import Court
from orders.documents import Order
from products.documents import Product
from reviews.documents import Review


def get_review_by_id(review_id):
    try:
        return Review.objects(
            id=ObjectId(review_id)
        ).first()
    except Exception:
        return None


def get_product_by_id(product_id):
    try:
        return Product.objects(
            id=ObjectId(product_id)
        ).first()
    except Exception:
        return None


def get_court_by_id(court_id):
    try:
        return Court.objects(
            id=ObjectId(court_id)
        ).first()
    except Exception:
        return None


def parse_rating(value):
    try:
        rating = int(value)

        if rating < 1 or rating > 5:
            return None

        return rating
    except (TypeError, ValueError):
        return None


def user_completed_product_order(user, product_id):
    orders = Order.objects(
        user=user,
        status="completed",
    )

    for order in orders:
        for item in order.items:
            if str(item.product_id) == str(product_id):
                return True

    return False


def user_completed_court_booking(user, court_id):
    try:
        booking = Booking.objects(
            user=user,
            court=ObjectId(court_id),
            status="completed",
        ).first()

        return booking is not None
    except Exception:
        return False


def validate_review_permission(
    user,
    target_type,
    target_id,
):
    if target_type == "product":
        product = get_product_by_id(target_id)

        if not product:
            return (
                None,
                "Product not found",
                status.HTTP_404_NOT_FOUND,
            )

        if not user_completed_product_order(
            user,
            target_id,
        ):
            return (
                None,
                (
                    "You can only review products "
                    "from completed orders"
                ),
                status.HTTP_403_FORBIDDEN,
            )

        return product, None, None

    if target_type == "court":
        court = get_court_by_id(target_id)

        if not court:
            return (
                None,
                "Court not found",
                status.HTTP_404_NOT_FOUND,
            )

        if not user_completed_court_booking(
            user,
            target_id,
        ):
            return (
                None,
                (
                    "You can only review courts "
                    "from completed bookings"
                ),
                status.HTTP_403_FORBIDDEN,
            )

        return court, None, None

    return (
        None,
        "Invalid target_type",
        status.HTTP_400_BAD_REQUEST,
    )


class ReviewListCreateView(APIView):
    def get(self, request):
        reviews = Review.objects(
            is_active=True
        )

        target_type = request.query_params.get(
            "target_type"
        )

        target_id = request.query_params.get(
            "target_id"
        )

        rating = request.query_params.get(
            "rating"
        )

        if target_type:
            if target_type not in Review.TARGET_TYPE_CHOICES:
                return Response(
                    {
                        "message": "Invalid target_type",
                        "allowed_target_types": list(
                            Review.TARGET_TYPE_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reviews = reviews.filter(
                target_type=target_type
            )

        if target_id:
            reviews = reviews.filter(
                target_id=target_id
            )

        if rating:
            parsed_rating = parse_rating(rating)

            if parsed_rating is None:
                return Response(
                    {
                        "message": (
                            "rating must be between 1 and 5"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reviews = reviews.filter(
                rating=parsed_rating
            )

        return Response(
            {
                "message": "Get reviews successfully",
                "data": [
                    review.to_json_data()
                    for review in reviews
                ],
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        target_type = data.get("target_type")
        target_id = data.get("target_id")
        rating = parse_rating(
            data.get("rating")
        )
        comment = data.get(
            "comment",
            "",
        )

        if (
            not target_type
            or not target_id
            or rating is None
        ):
            return Response(
                {
                    "message": (
                        "target_type, target_id and "
                        "rating are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_type not in Review.TARGET_TYPE_CHOICES:
            return Response(
                {
                    "message": "Invalid target_type",
                    "allowed_target_types": list(
                        Review.TARGET_TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not ObjectId.is_valid(target_id):
            return Response(
                {
                    "message": "Invalid target_id"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(comment, str):
            return Response(
                {
                    "message": "comment must be a string"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = comment.strip()

        if len(comment) > 2000:
            return Response(
                {
                    "message": (
                        "comment cannot exceed "
                        "2000 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _, error_message, error_status = (
            validate_review_permission(
                user,
                target_type,
                target_id,
            )
        )

        if error_message:
            return Response(
                {"message": error_message},
                status=error_status,
            )

        existing_review = Review.objects(
            user=user,
            target_type=target_type,
            target_id=target_id,
        ).first()

        if existing_review:
            if existing_review.is_active:
                return Response(
                    {
                        "message": (
                            "You have already reviewed "
                            "this target"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.is_active = True
            existing_review.updated_at = (
                datetime.utcnow()
            )
            existing_review.save()

            return Response(
                {
                    "message": (
                        "Restore review successfully"
                    ),
                    "data": (
                        existing_review.to_json_data()
                    ),
                },
                status=status.HTTP_200_OK,
            )

        try:
            review = Review(
                user=user,
                target_type=target_type,
                target_id=target_id,
                rating=rating,
                comment=comment,
                is_active=True,
            )
            review.save()

        except NotUniqueError:
            return Response(
                {
                    "message": (
                        "You have already reviewed "
                        "this target"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Create review successfully",
                "data": review.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class ReviewDetailView(APIView):
    def get(self, request, review_id):
        review = get_review_by_id(review_id)

        if not review or not review.is_active:
            return Response(
                {"message": "Review not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": (
                    "Get review detail successfully"
                ),
                "data": review.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def put(self, request, review_id):
        review = get_review_by_id(review_id)

        if not review or not review.is_active:
            return Response(
                {"message": "Review not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and review.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        if data.get("rating") is not None:
            rating = parse_rating(
                data.get("rating")
            )

            if rating is None:
                return Response(
                    {
                        "message": (
                            "rating must be between 1 and 5"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review.rating = rating

        if data.get("comment") is not None:
            comment = data.get("comment")

            if not isinstance(comment, str):
                return Response(
                    {
                        "message": (
                            "comment must be a string"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            comment = comment.strip()

            if len(comment) > 2000:
                return Response(
                    {
                        "message": (
                            "comment cannot exceed "
                            "2000 characters"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review.comment = comment

        review.updated_at = datetime.utcnow()
        review.save()

        return Response(
            {
                "message": "Update review successfully",
                "data": review.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def delete(self, request, review_id):
        review = get_review_by_id(review_id)

        if not review or not review.is_active:
            return Response(
                {"message": "Review not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and review.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        review.is_active = False
        review.updated_at = datetime.utcnow()
        review.save()

        return Response(
            {
                "message": "Delete review successfully"
            },
            status=status.HTTP_200_OK,
        )


class ReviewSummaryView(APIView):
    def get(self, request):
        target_type = request.query_params.get(
            "target_type"
        )

        target_id = request.query_params.get(
            "target_id"
        )

        if not target_type or not target_id:
            return Response(
                {
                    "message": (
                        "target_type and target_id "
                        "are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_type not in Review.TARGET_TYPE_CHOICES:
            return Response(
                {
                    "message": "Invalid target_type",
                    "allowed_target_types": list(
                        Review.TARGET_TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reviews = Review.objects(
            target_type=target_type,
            target_id=target_id,
            is_active=True,
        )

        total_reviews = reviews.count()

        if total_reviews == 0:
            return Response(
                {
                    "message": (
                        "Get review summary successfully"
                    ),
                    "data": {
                        "target_type": target_type,
                        "target_id": target_id,
                        "average_rating": 0,
                        "total_reviews": 0,
                        "rating_breakdown": {
                            "1": 0,
                            "2": 0,
                            "3": 0,
                            "4": 0,
                            "5": 0,
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

        total_rating = sum(
            review.rating
            for review in reviews
        )

        rating_breakdown = {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0,
        }

        for review in reviews:
            rating_breakdown[
                str(review.rating)
            ] += 1

        average_rating = round(
            total_rating / total_reviews,
            2,
        )

        return Response(
            {
                "message": (
                    "Get review summary successfully"
                ),
                "data": {
                    "target_type": target_type,
                    "target_id": target_id,
                    "average_rating": average_rating,
                    "total_reviews": total_reviews,
                    "rating_breakdown": (
                        rating_breakdown
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class MyReviewListView(APIView):
    @login_required
    def get(self, request):
        reviews = Review.objects(
            user=request.current_user,
            is_active=True,
        )

        return Response(
            {
                "message": (
                    "Get my reviews successfully"
                ),
                "data": [
                    review.to_json_data()
                    for review in reviews
                ],
            },
            status=status.HTTP_200_OK,
        )


class AdminReviewListView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if user.role not in ["admin", "staff"]:
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        reviews = Review.objects()

        is_active = request.query_params.get(
            "is_active"
        )

        if is_active is not None:
            value = is_active.strip().lower()

            if value == "true":
                reviews = reviews.filter(
                    is_active=True
                )
            elif value == "false":
                reviews = reviews.filter(
                    is_active=False
                )
            else:
                return Response(
                    {
                        "message": (
                            "is_active must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "message": (
                    "Get all reviews successfully"
                ),
                "data": [
                    review.to_json_data()
                    for review in reviews
                ],
            },
            status=status.HTTP_200_OK,
        )
