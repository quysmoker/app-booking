from datetime import datetime

import bcrypt
from bson import ObjectId
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from mongoengine.queryset.visitor import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import role_required
from users.documents import User


def get_user_by_id(user_id):
    try:
        return User.objects(
            id=ObjectId(user_id)
        ).first()
    except Exception:
        return None


def normalize_email(value):
    email = str(
        value or ""
    ).strip().lower()

    try:
        validate_email(email)
    except ValidationError:
        return None

    return email


def parse_boolean(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized_value = (
            value.strip().lower()
        )

        if normalized_value == "true":
            return True

        if normalized_value == "false":
            return False

    return None


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


class UserListCreateView(APIView):
    @role_required(["admin", "staff"])
    def get(self, request):
        users = User.objects()

        role = request.query_params.get(
            "role"
        )

        is_active = request.query_params.get(
            "is_active"
        )

        search = str(
            request.query_params.get(
                "search",
                "",
            )
        ).strip()

        if role:
            if role not in User.ROLE_CHOICES:
                return Response(
                    {
                        "message": (
                            "Invalid user role"
                        ),
                        "allowed_roles": list(
                            User.ROLE_CHOICES
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            users = users.filter(role=role)

        if is_active is not None:
            active_value = parse_boolean(
                is_active
            )

            if active_value is None:
                return Response(
                    {
                        "message": (
                            "is_active must be "
                            "true or false"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            users = users.filter(
                is_active=active_value
            )

        if search:
            users = users.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        user_data = [
            user.to_json_data()
            for user in users
        ]

        return Response(
            {
                "message": (
                    "Get users successfully"
                ),
                "total": len(user_data),
                "data": user_data,
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin"])
    def post(self, request):
        data = request.data

        full_name = str(
            data.get("full_name", "")
        ).strip()

        email = normalize_email(
            data.get("email")
        )

        password = data.get("password")

        phone = str(
            data.get("phone", "")
        ).strip()

        avatar = str(
            data.get("avatar", "")
        ).strip()

        role = data.get(
            "role",
            "user",
        )

        if (
            not full_name
            or not email
            or not password
        ):
            return Response(
                {
                    "message": (
                        "full_name, valid email and "
                        "password are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = str(password)

        if len(password) < 8:
            return Response(
                {
                    "message": (
                        "password must contain at least "
                        "8 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in User.ROLE_CHOICES:
            return Response(
                {
                    "message": "Invalid user role",
                    "allowed_roles": list(
                        User.ROLE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = User.objects(
            email=email
        ).first()

        if existing_user:
            return Response(
                {"message": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_value = True

        if data.get("is_active") is not None:
            active_value = parse_boolean(
                data.get("is_active")
            )

            if active_value is None:
                return Response(
                    {
                        "message": (
                            "is_active must be "
                            "true or false"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hash_password(password),
            role=role,
            avatar=avatar,
            is_active=active_value,
        )

        user.save()

        return Response(
            {
                "message": (
                    "Create user successfully"
                ),
                "data": user.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(APIView):
    @role_required(["admin", "staff"])
    def get(self, request, user_id):
        user = get_user_by_id(user_id)

        if not user:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": (
                    "Get user detail successfully"
                ),
                "data": user.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin"])
    def put(self, request, user_id):
        user = get_user_by_id(user_id)

        if not user:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data
        current_user = request.current_user

        if data.get("is_active") is not None:
            return Response(
                {
                    "message": (
                        "Use the user status endpoint "
                        "to change is_active"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data.get("full_name") is not None:
            full_name = str(
                data.get("full_name")
            ).strip()

            if not full_name:
                return Response(
                    {
                        "message": (
                            "full_name cannot be empty"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            user.full_name = full_name

        if data.get("email") is not None:
            email = normalize_email(
                data.get("email")
            )

            if not email:
                return Response(
                    {
                        "message": (
                            "Invalid email address"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            duplicate_user = User.objects(
                email=email,
                id__ne=user.id,
            ).first()

            if duplicate_user:
                return Response(
                    {
                        "message": (
                            "Email already exists"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            user.email = email

        if data.get("role") is not None:
            role = data.get("role")

            if role not in User.ROLE_CHOICES:
                return Response(
                    {
                        "message": (
                            "Invalid user role"
                        ),
                        "allowed_roles": list(
                            User.ROLE_CHOICES
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            if (
                user.id == current_user.id
                and role != "admin"
            ):
                return Response(
                    {
                        "message": (
                            "Admin cannot change "
                            "their own role"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            user.role = role

        if data.get("password") is not None:
            password = str(
                data.get("password")
            )

            if len(password) < 8:
                return Response(
                    {
                        "message": (
                            "password must contain "
                            "at least 8 characters"
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            user.password = hash_password(
                password
            )

        if data.get("phone") is not None:
            user.phone = str(
                data.get("phone")
            ).strip()

        if data.get("avatar") is not None:
            user.avatar = str(
                data.get("avatar")
            ).strip()

        user.updated_at = datetime.utcnow()
        user.save()

        return Response(
            {
                "message": (
                    "Update user successfully"
                ),
                "data": user.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    patch = put


class UserStatusUpdateView(APIView):
    @role_required(["admin"])
    def patch(self, request, user_id):
        user = get_user_by_id(user_id)

        if not user:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        active_value = parse_boolean(
            request.data.get("is_active")
        )

        if active_value is None:
            return Response(
                {
                    "message": (
                        "is_active must be "
                        "true or false"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            user.id == request.current_user.id
            and not active_value
        ):
            return Response(
                {
                    "message": (
                        "Admin cannot deactivate "
                        "their own account"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = active_value
        user.updated_at = datetime.utcnow()
        user.save()

        return Response(
            {
                "message": (
                    "Update user status successfully"
                ),
                "data": user.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
