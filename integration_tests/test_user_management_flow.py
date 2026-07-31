import bcrypt

from integration_tests.base import (
    IntegrationTestBase,
)
from users.documents import User


class UserManagementIntegrationTest(
    IntegrationTestBase
):
    def test_admin_can_list_users(self):
        self.login_admin()

        response = self.client.get(
            "/api/users/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.assertEqual(
            response.data["total"],
            3,
        )

    def test_staff_can_list_users(self):
        self.login_staff()

        response = self.client.get(
            "/api/users/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

    def test_normal_user_cannot_list_users(
        self,
    ):
        self.login_user()

        response = self.client.get(
            "/api/users/"
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_admin_can_create_staff_account(
        self,
    ):
        self.login_admin()

        response = self.client.post(
            "/api/users/",
            {
                "full_name": "New Staff",
                "email": "NEWSTAFF@TEST.COM",
                "phone": "0900000000",
                "password": "Test123456",
                "role": "staff",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["email"],
            "newstaff@test.com",
        )

        self.assertEqual(
            response.data["data"]["role"],
            "staff",
        )

        self.assertNotIn(
            "password",
            response.data["data"],
        )

        created_user = User.objects(
            email="newstaff@test.com"
        ).first()

        self.assertIsNotNone(
            created_user
        )

        self.assertTrue(
            bcrypt.checkpw(
                b"Test123456",
                created_user.password.encode(
                    "utf-8"
                ),
            )
        )

    def test_staff_cannot_create_user(self):
        self.login_staff()

        response = self.client.post(
            "/api/users/",
            {
                "full_name": (
                    "Unauthorized User"
                ),
                "email": (
                    "unauthorized@test.com"
                ),
                "password": "Test123456",
                "role": "user",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_admin_can_update_user_role(self):
        self.login_admin()

        response = self.client.put(
            f"/api/users/{self.user.id}/",
            {
                "full_name": (
                    self.user.full_name
                ),
                "role": "staff",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.user.reload()

        self.assertEqual(
            self.user.role,
            "staff",
        )

    def test_admin_can_deactivate_user(self):
        self.login_admin()

        response = self.client.patch(
            (
                f"/api/users/{self.user.id}"
                "/status/"
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.user.reload()

        self.assertFalse(
            self.user.is_active
        )

    def test_admin_cannot_deactivate_self(
        self,
    ):
        self.login_admin()

        response = self.client.patch(
            (
                f"/api/users/{self.admin.id}"
                "/status/"
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

        self.admin.reload()

        self.assertTrue(
            self.admin.is_active
        )

    def test_admin_can_search_and_filter_users(
        self,
    ):
        self.login_admin()

        response = self.client.get(
            (
                "/api/users/"
                "?search=staff&role=staff"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.assertEqual(
            response.data["total"],
            1,
        )

        self.assertEqual(
            response.data["data"][0]["email"],
            "staff@test.com",
        )
