from integration_tests.base import (
    IntegrationTestBase,
)


class PermissionIntegrationTest(
    IntegrationTestBase
):
    def test_normal_user_cannot_access_dashboard(
        self,
    ):
        self.login_user()

        response = self.client.get(
            "/api/dashboard/"
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_staff_can_access_dashboard(self):
        self.login_staff()

        response = self.client.get(
            "/api/dashboard/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

    def test_admin_can_access_dashboard(self):
        self.login_admin()

        response = self.client.get(
            "/api/dashboard/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

    def test_user_cannot_broadcast_notification(
        self,
    ):
        self.login_user()

        response = self.client.post(
            "/api/notifications/admin/broadcast/",
            {
                "notification_type": "system",
                "title": "Test broadcast",
                "message": "Test message",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_admin_can_broadcast_notification(
        self,
    ):
        self.login_admin()

        response = self.client.post(
            "/api/notifications/admin/broadcast/",
            {
                "notification_type": "system",
                "title": "System notification",
                "message": (
                    "Integration test notification"
                ),
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [200, 201],
            response.data,
        )
