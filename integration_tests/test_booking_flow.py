from datetime import datetime, timedelta

from integration_tests.base import IntegrationTestBase
from bookings.documents import Booking
from courts.documents import Court
from notifications.documents import Notification


class BookingIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Court.drop_collection()
        Booking.drop_collection()
        Notification.drop_collection()

        self.court = Court(
            name="Court Integration Test",
            sport_type="pickleball",
            price_per_hour=100000,
            status="available",
            is_active=True,
        ).save()

    def tearDown(self):
        Notification.drop_collection()
        Booking.drop_collection()
        Court.drop_collection()

        super().tearDown()

    def test_create_booking_successfully(self):
        self.login_user()

        start_time = (
            datetime.utcnow()
            + timedelta(days=1)
        )

        end_time = start_time + timedelta(hours=2)

        response = self.client.post(
            "/api/bookings/",
            {
                "court_id": str(self.court.id),
                "booking_date": (
                    start_time.strftime("%Y-%m-%d")
                ),
                "start_time": (
                    start_time.strftime("%H:%M")
                ),
                "end_time": (
                    end_time.strftime("%H:%M")
                ),
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [200, 201],
            response.data,
        )

        booking = Booking.objects(
            user=self.user
        ).first()

        self.assertIsNotNone(booking)

    def test_cannot_create_overlapping_booking(self):
        self.login_user()

        booking_date = (
            datetime.utcnow()
            + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        payload = {
            "court_id": str(self.court.id),
            "booking_date": booking_date,
            "start_time": "08:00",
            "end_time": "10:00",
        }

        first_response = self.client.post(
            "/api/bookings/",
            payload,
            format="json",
        )

        self.assertIn(
            first_response.status_code,
            [200, 201],
            first_response.data,
        )

        second_response = self.client.post(
            "/api/bookings/",
            payload,
            format="json",
        )

        self.assertIn(
            second_response.status_code,
            [400, 409],
            second_response.data,
        )

    def test_booking_creation_creates_notification(self):
        self.login_user()

        booking_date = (
            datetime.utcnow()
            + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        response = self.client.post(
            "/api/bookings/",
            {
                "court_id": str(self.court.id),
                "booking_date": booking_date,
                "start_time": "12:00",
                "end_time": "14:00",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [200, 201],
            response.data,
        )

        notification = Notification.objects(
            recipient=self.user,
            notification_type="booking",
        ).first()

        self.assertIsNotNone(
            notification,
            (
                "Tạo booking thành công nhưng không "
                "tạo notification"
            ),
        )
