from bson import ObjectId

from integration_tests.base import IntegrationTestBase
from reviews.documents import Review


class ReviewManagementIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Review.drop_collection()

        self.active_review = Review(
            user=self.user,
            target_type="product",
            target_id=str(ObjectId()),
            rating=5,
            comment="Sản phẩm rất tốt",
            is_active=True,
        ).save()

        self.inactive_review = Review(
            user=self.staff,
            target_type="court",
            target_id=str(ObjectId()),
            rating=3,
            comment="Sân cần cải thiện",
            is_active=False,
        ).save()

    def tearDown(self):
        Review.drop_collection()
        super().tearDown()

    def test_user_cannot_get_admin_review_list(self):
        self.login_user()

        response = self.client.get(
            "/api/reviews/admin/all/"
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_staff_can_get_active_and_inactive_reviews(self):
        self.login_staff()

        response = self.client.get(
            "/api/reviews/admin/all/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )
        self.assertEqual(
            len(response.data["data"]),
            2,
        )

    def test_admin_can_filter_and_search_reviews(self):
        self.login_admin()

        response = self.client.get(
            "/api/reviews/admin/all/",
            {
                "target_type": "product",
                "rating": "5",
                "is_active": "true",
                "search": "user@test.com",
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
            str(self.active_review.id),
        )

    def test_admin_can_hide_and_restore_review(self):
        self.login_admin()

        hide_response = self.client.patch(
            (
                f"/api/reviews/{self.active_review.id}"
                "/status/"
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
                f"/api/reviews/{self.active_review.id}"
                "/status/"
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

    def test_status_update_validates_role_and_payload(self):
        self.login_user()

        denied_response = self.client.patch(
            (
                f"/api/reviews/{self.active_review.id}"
                "/status/"
            ),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(
            denied_response.status_code,
            403,
            denied_response.data,
        )

        self.login_staff()

        invalid_response = self.client.patch(
            (
                f"/api/reviews/{self.active_review.id}"
                "/status/"
            ),
            {"is_active": "false"},
            format="json",
        )

        self.assertEqual(
            invalid_response.status_code,
            400,
            invalid_response.data,
        )
