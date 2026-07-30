import bcrypt
from django.test import TestCase
from rest_framework.test import APIClient

from users.documents import User


class IntegrationTestBase(TestCase):
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    def setUp(self):
        self.client = APIClient()

        User.drop_collection()

        self.user = User(
            email="user@test.com",
            full_name="Integration User",
            role="user",
            password=self.hash_password(
                "Test123456"
            ),
        )
        self.user.save()

        self.staff = User(
            email="staff@test.com",
            full_name="Integration Staff",
            role="staff",
            password=self.hash_password(
                "Test123456"
            ),
        )
        self.staff.save()

        self.admin = User(
            email="admin@test.com",
            full_name="Integration Admin",
            role="admin",
            password=self.hash_password(
                "Test123456"
            ),
        )
        self.admin.save()

    def tearDown(self):
        User.drop_collection()

    def login(
        self,
        email,
        password="Test123456",
    ):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": email,
                "password": password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        token = (
            response.data.get("access_token")
            or response.data.get("token")
            or response.data.get(
                "data",
                {},
            ).get("access_token")
            or response.data.get(
                "data",
                {},
            ).get("token")
        )

        self.assertIsNotNone(
            token,
            (
                "Không tìm thấy access token "
                "trong response login"
            ),
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {token}"
            )
        )

        return response

    def login_user(self):
        return self.login("user@test.com")

    def login_staff(self):
        return self.login("staff@test.com")

    def login_admin(self):
        return self.login("admin@test.com")

    def clear_authentication(self):
        self.client.credentials()
