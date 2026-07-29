from integration_tests.base import IntegrationTestBase
from notifications.documents import Notification


class NotificationIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()
        Notification.drop_collection()

    def tearDown(self):
        Notification.drop_collection()
        super().tearDown()

    def create_notification(self):
        return Notification(
            recipient=self.user,
            notification_type="system",
            title="Thông báo kiểm thử",
            message="Nội dung kiểm thử tích hợp",
            is_read=False,
            is_active=True,
        ).save()

    def test_user_can_get_own_notifications(self):
        self.create_notification()
        self.login_user()

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        data = response.data.get("data", [])

        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["title"],
            "Thông báo kiểm thử",
        )

    def test_mark_notification_as_read(self):
        notification = self.create_notification()
        self.login_user()

        response = self.client.patch(
            (
                f"/api/notifications/"
                f"{notification.id}/read/"
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        notification.reload()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_all_notifications_as_read(self):
        self.create_notification()

        Notification(
            recipient=self.user,
            notification_type="order",
            title="Order notification",
            message="Order message",
            is_read=False,
        ).save()

        self.login_user()

        response = self.client.patch(
            "/api/notifications/mark-all-read/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        unread_count = Notification.objects(
            recipient=self.user,
            is_read=False,
            is_active=True,
        ).count()

        self.assertEqual(unread_count, 0)

    def test_user_cannot_read_another_users_notification(
        self,
    ):
        notification = Notification(
            recipient=self.staff,
            notification_type="system",
            title="Private notification",
            message="Only staff can see this",
        ).save()

        self.login_user()

        response = self.client.get(
            (
                f"/api/notifications/"
                f"{notification.id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_delete_notification_is_soft_delete(self):
        notification = self.create_notification()
        self.login_user()

        response = self.client.delete(
            (
                f"/api/notifications/"
                f"{notification.id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        notification.reload()

        self.assertFalse(notification.is_active)
