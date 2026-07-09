from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from users.documents import User
from authentication.jwt_utils import decode_token
from bson import ObjectId


def get_current_user(request):
    auth_header = request.headers.get("Authorization")
   

    if not auth_header:
        print("No Authorization header")
        return None

    try:
        token_type, token = auth_header.split(" ")
    except ValueError:
        print("Header format error")
        return None

   

    payload = decode_token(token)


    if not payload:
        print("Decode token failed")
        return None

    user_id = payload.get("user_id")

    if not user_id:
        print("No user_id in token")
        return None

    try:
        user = User.objects(id=ObjectId(user_id)).first()
    except Exception as e:
        print("ObjectId error:", e)
        return None



    if not user:
        print("User not found")
        return None

    if not user.is_active:
        print("User inactive")
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
        return view_func(self, request, *args, **kwargs)

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
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator
