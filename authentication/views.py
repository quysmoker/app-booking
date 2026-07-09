import bcrypt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from users.documents import User
from authentication.jwt_utils import generate_token
from authentication.permissions import login_required


class RegisterView(APIView):
    def post(self, request):
        data = request.data

        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone", "")
        password = data.get("password")
        role = data.get("role", "user")

        if not full_name or not email or not password:
            return Response(
                {"message": "full_name, email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ["admin", "staff", "user"]:
            return Response(
                {"message": "Invalid role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = User.objects(email=email).first()

        if existing_user:
            return Response(
                {"message": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hashed_password,
            role=role,
        )
        user.save()

        token = generate_token(user)

        return Response(
            {
                "message": "Register successfully",
                "token": token,
                "user": user.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request):
        data = request.data

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response(
                {"message": "email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects(email=email).first()

        if not user:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        is_valid_password = bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8")
        )

        if not is_valid_password:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"message": "Account is locked"},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = generate_token(user)

        return Response(
            {
                "message": "Login successfully",
                "token": token,
                "user": user.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    @login_required
    def get(self, request):
        return Response(
            {
                "message": "Get profile successfully",
                "user": request.current_user.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
