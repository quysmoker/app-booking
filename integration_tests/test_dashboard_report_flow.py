from datetime import datetime

from bson import ObjectId

from bookings.documents import Booking
from courts.documents import Court
from integration_tests.base import IntegrationTestBase
from orders.documents import Order, OrderItem


class DashboardReportIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Booking.drop_collection()
        Order.drop_collection()
        Court.drop_collection()

        self.court = Court(
            name="Report Test Court",
            sport_type="pickleball",
            location="Report Test Location",
            price_per_hour=200000,
            status="available",
            is_active=True,
        ).save()

        Booking(
            user=self.user,
            court=self.court,
            start_time=datetime(2026, 7, 10, 8, 0),
            end_time=datetime(2026, 7, 10, 9, 0),
            total_price=200000,
            status="completed",
            created_at=datetime(2026, 7, 10, 7, 0),
        ).save()

        Booking(
            user=self.user,
            court=self.court,
            start_time=datetime(2026, 7, 11, 8, 0),
            end_time=datetime(2026, 7, 11, 9, 0),
            total_price=200000,
            status="cancelled",
            created_at=datetime(2026, 7, 11, 7, 0),
        ).save()

        Booking(
            user=self.user,
            court=self.court,
            start_time=datetime(2026, 6, 30, 8, 0),
            end_time=datetime(2026, 6, 30, 9, 0),
            total_price=999000,
            status="completed",
            created_at=datetime(2026, 6, 30, 7, 0),
        ).save()

        self.create_order(
            code="ORD-REPORT-001",
            status="completed",
            total_amount=300000,
            quantity=2,
            created_at=datetime(2026, 7, 10, 10, 0),
        )

        self.create_order(
            code="ORD-REPORT-002",
            status="cancelled",
            total_amount=100000,
            quantity=1,
            created_at=datetime(2026, 7, 11, 10, 0),
        )

        self.create_order(
            code="ORD-REPORT-003",
            status="completed",
            total_amount=999000,
            quantity=1,
            created_at=datetime(2026, 8, 1, 10, 0),
        )

    def create_order(
        self,
        code,
        status,
        total_amount,
        quantity,
        created_at,
    ):
        return Order(
            code=code,
            user=self.user,
            items=[
                OrderItem(
                    product_id=str(ObjectId()),
                    product_name="Report Test Product",
                    quantity=quantity,
                    unit_price=(
                        total_amount / quantity
                    ),
                    subtotal=total_amount,
                )
            ],
            recipient_name="Integration User",
            recipient_phone="0900000000",
            shipping_address="Report Test Address",
            subtotal=total_amount,
            total_amount=total_amount,
            status=status,
            payment_method="cod",
            payment_status="paid",
            created_at=created_at,
        ).save()

    def tearDown(self):
        Booking.drop_collection()
        Order.drop_collection()
        Court.drop_collection()
        super().tearDown()

    def test_user_cannot_access_dashboard_report(self):
        self.login_user()

        response = self.client.get(
            "/api/dashboard/reports/"
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_report_rejects_invalid_date_range(self):
        self.login_admin()

        response = self.client.get(
            "/api/dashboard/reports/",
            {
                "start_date": "2026-07-31",
                "end_date": "2026-07-01",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

    def test_admin_can_get_report_summary_for_date_range(self):
        self.login_admin()

        response = self.client.get(
            "/api/dashboard/reports/",
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-31",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        summary = response.data["data"]["summary"]

        self.assertEqual(summary["total_bookings"], 2)
        self.assertEqual(summary["total_orders"], 2)
        self.assertEqual(summary["booking_revenue"], 200000)
        self.assertEqual(summary["order_revenue"], 300000)
        self.assertEqual(summary["total_revenue"], 500000)

    def test_report_returns_daily_and_top_statistics(self):
        self.login_staff()

        response = self.client.get(
            "/api/dashboard/reports/",
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-31",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        data = response.data["data"]

        self.assertEqual(
            data["daily_revenue"][0]["total_revenue"],
            500000,
        )
        self.assertEqual(
            data["top_courts"][0]["court_name"],
            self.court.name,
        )
        self.assertEqual(
            data["top_courts"][0]["booking_count"],
            1,
        )
        self.assertEqual(
            data["top_products"][0]["product_name"],
            "Report Test Product",
        )
        self.assertEqual(
            data["top_products"][0]["quantity"],
            2,
        )
