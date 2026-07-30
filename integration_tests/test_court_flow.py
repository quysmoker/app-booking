from courts.documents import Court
from integration_tests.base import (
    IntegrationTestBase,
)


class CourtIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()
        Court.drop_collection()

    def tearDown(self):
        Court.drop_collection()
        super().tearDown()

    def test_admin_can_create_court_with_sport_and_status(
        self,
    ):
        self.login_admin()

        response = self.client.post(
            "/api/courts/",
            {
                "name": "Pickleball Court 01",
                "location": "123 Test Street",
                "sport_type": "pickleball",
                "status": "available",
                "price_per_hour": 120000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["location"],
            "123 Test Street",
        )

        self.assertEqual(
            response.data["data"]["sport_type"],
            "pickleball",
        )

    def test_normal_user_cannot_create_court(
        self,
    ):
        self.login_user()

        response = self.client.post(
            "/api/courts/",
            {
                "name": "Unauthorized Court",
                "location": "123 Test Street",
                "sport_type": "tennis",
                "status": "available",
                "price_per_hour": 150000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_create_court_accepts_legacy_address_field(
        self,
    ):
        self.login_staff()

        response = self.client.post(
            "/api/courts/",
            {
                "name": "Badminton Court 01",
                "address": "456 Legacy Address",
                "sport_type": "badminton",
                "status": "maintenance",
                "price_per_hour": 90000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertEqual(
            response.data["data"]["location"],
            "456 Legacy Address",
        )
