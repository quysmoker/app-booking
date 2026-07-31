from integration_tests.base import IntegrationTestBase
from notifications.documents import Notification
from users.documents import User


class NotificationManagementIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Notification.drop_collection()

        self.notification = Notification(
            recipient=self.user,
            notification_type="system",
            title="Thông báo quản trị",
            message="Nội dung dùng để tìm kiếm",
            is_read=False,
            is_active=True,
        ).save()

    def tearDown(self):
        Notification.drop_collection()
        super().tearDown()

    def test_user_cannot_get_admin_notification_list(
        self,
    ):
        self.login_user()

        response = self.client.get(
            "/api/notifications/admin/all/"
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_admin_can_create_notification_for_user(
        self,
    ):
        self.login_admin()

        response = self.client.post(
            "/api/notifications/admin/create/",
            {
                "recipient_id": str(self.staff.id),
                "notification_type": "booking",
                "title": "Lịch đặt sân mới",
                "message": (
                    "Bạn có một lịch đặt sân mới"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["recipient"]["id"],
            str(self.staff.id),
        )

    def test_staff_can_search_and_filter_notifications(
        self,
    ):
        self.login_staff()

        response = self.client.get(
            "/api/notifications/admin/all/",
            {
                "search": "user@test.com",
                "notification_type": "system",
                "is_read": "false",
                "is_active": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.assertEqual(
            len(response.data["data"]),
            1,
        )

        self.assertEqual(
            response.data["data"][0]["id"],
            str(self.notification.id),
        )

    def test_admin_can_broadcast_to_active_users_by_role(
        self,
    ):
        User(
            email="inactive@test.com",
            full_name="Inactive User",
            role="user",
            password=self.hash_password(
                "Test123456"
            ),
            is_active=False,
        ).save()

        self.login_admin()

        response = self.client.post(
            "/api/notifications/admin/broadcast/",
            {
                "recipient_role": "user",
                "notification_type": "voucher",
                "title": "Voucher mới",
                "message": (
                    "Voucher dành cho khách hàng"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["sent_count"],
            1,
        )

        created_notification = (
            Notification.objects(
                title="Voucher mới"
            ).first()
        )

        self.assertIsNotNone(
            created_notification
        )

        self.assertEqual(
            created_notification.recipient.id,
            self.user.id,
        )

    def test_admin_can_hide_and_restore_notification(
        self,
    ):
        self.login_admin()

        hide_response = self.client.patch(
            (
                f"/api/notifications/"
                f"{self.notification.id}/status/"
            ),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(
            hide_response.status_code,
            200,
            hide_response.data,
        )

        self.assertFalse(
            hide_response.data["data"]["is_active"]
        )

        restore_response = self.client.patch(
            (
                f"/api/notifications/"
                f"{self.notification.id}/status/"
            ),
            {"is_active": True},
            format="json",
        )

        self.assertEqual(
            restore_response.status_code,
            200,
            restore_response.data,
        )

        self.assertTrue(
            restore_response.data["data"]["is_active"]
        )

    def test_broadcast_validates_recipient_role(self):
        self.login_admin()

        response = self.client.post(
            "/api/notifications/admin/broadcast/",
            {
                "recipient_role": "manager",
                "title": "Invalid role",
                "message": "Invalid role test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )
