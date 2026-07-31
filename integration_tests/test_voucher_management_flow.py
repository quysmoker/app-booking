from datetime import datetime, timedelta

from integration_tests.base import (
    IntegrationTestBase,
)
from vouchers.documents import Voucher


class VoucherManagementIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Voucher.drop_collection()

        now = datetime.utcnow()

        self.available_voucher = Voucher(
            code="ACTIVE10",
            name="Active Voucher",
            discount_type="percentage",
            discount_value=10,
            min_order_value=100000,
            start_date=(
                now - timedelta(days=1)
            ),
            end_date=(
                now + timedelta(days=7)
            ),
            usage_limit=100,
            is_active=True,
        ).save()

        self.inactive_voucher = Voucher(
            code="INACTIVE50",
            name="Inactive Voucher",
            discount_type="fixed",
            discount_value=50000,
            start_date=(
                now - timedelta(days=1)
            ),
            end_date=(
                now + timedelta(days=7)
            ),
            is_active=False,
        ).save()

        self.upcoming_voucher = Voucher(
            code="UPCOMING20",
            name="Upcoming Voucher",
            discount_type="percentage",
            discount_value=20,
            start_date=(
                now + timedelta(days=1)
            ),
            end_date=(
                now + timedelta(days=8)
            ),
            is_active=True,
        ).save()

    def tearDown(self):
        Voucher.drop_collection()
        super().tearDown()

    def test_public_list_only_returns_available_vouchers(
        self,
    ):
        response = self.client.get(
            "/api/vouchers/"
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
            response.data["data"][0]["code"],
            "ACTIVE10",
        )

    def test_admin_list_returns_all_vouchers(
        self,
    ):
        self.login_admin()

        response = self.client.get(
            "/api/vouchers/"
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

    def test_staff_list_returns_all_vouchers(
        self,
    ):
        self.login_staff()

        response = self.client.get(
            "/api/vouchers/"
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

    def test_admin_can_search_and_filter_vouchers(
        self,
    ):
        self.login_admin()

        response = self.client.get(
            (
                "/api/vouchers/"
                "?search=inactive"
                "&is_active=false"
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
            response.data["data"][0]["code"],
            "INACTIVE50",
        )

    def test_admin_can_create_voucher(self):
        self.login_admin()

        now = datetime.utcnow()

        response = self.client.post(
            "/api/vouchers/",
            {
                "code": "new15",
                "name": "New Voucher",
                "discount_type": "percentage",
                "discount_value": 15,
                "min_order_value": 200000,
                "start_date": now.isoformat(),
                "end_date": (
                    now + timedelta(days=5)
                ).isoformat(),
                "usage_limit": 20,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["code"],
            "NEW15",
        )

    def test_admin_can_reactivate_voucher(
        self,
    ):
        self.login_admin()

        response = self.client.patch(
            (
                f"/api/vouchers/"
                f"{self.inactive_voucher.id}"
                "/status/"
            ),
            {
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.inactive_voucher.reload()

        self.assertTrue(
            self.inactive_voucher.is_active
        )

    def test_normal_user_cannot_create_voucher(
        self,
    ):
        self.login_user()

        now = datetime.utcnow()

        response = self.client.post(
            "/api/vouchers/",
            {
                "code": "DENIED10",
                "name": "Denied Voucher",
                "discount_type": "percentage",
                "discount_value": 10,
                "start_date": now.isoformat(),
                "end_date": (
                    now + timedelta(days=1)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )
