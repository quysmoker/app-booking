

from functools import wraps

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response

from authentication.jwt_utils import decode_token
from users.documents import User


def get_current_user(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:
        token_type, token = auth_header.split(" ", 1)
    except ValueError:
        return None

    if token_type.lower() != "bearer" or not token.strip():
        return None

    payload = decode_token(token.strip())

    if not payload:
        return None

    user_id = payload.get("user_id")

    if not user_id:
        return None

    try:
        user = User.objects(
            id=ObjectId(user_id)
        ).first()
    except Exception:
        return None

    if not user:
        return None

    if not user.is_active:
        return None

    return user


def login_required(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user = get_current_user(request)

        if not user:
            return Response(
                {"message": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        request.current_user = user

        return view_func(
            self,
            request,
            *args,
            **kwargs,
        )

    return wrapper


def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            user = get_current_user(request)

            if not user:
                return Response(
                    {"message": "Unauthorized"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if user.role not in roles:
                return Response(
                    {"message": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            request.current_user = user

            return view_func(
                self,
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator
