from integration_tests.base import IntegrationTestBase
from orders.documents import Order
from products.documents import Product
from reviews.documents import Review


class ReviewIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Product.drop_collection()
        Order.drop_collection()
        Review.drop_collection()

        self.product = Product(
            name="Review Test Product",
            price=300000,
            stock=20,
            is_active=True,
        ).save()

    def tearDown(self):
        Review.drop_collection()
        Order.drop_collection()
        Product.drop_collection()

        super().tearDown()

    def test_user_cannot_review_without_completed_order(
        self,
    ):
        self.login_user()

        response = self.client.post(
            "/api/reviews/",
            {
                "target_type": "product",
                "target_id": str(self.product.id),
                "rating": 5,
                "comment": "Sản phẩm tốt",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [400, 403],
            response.data,
        )

    def test_rating_must_be_between_one_and_five(
        self,
    ):
        self.login_user()

        response = self.client.post(
            "/api/reviews/",
            {
                "target_type": "product",
                "target_id": str(self.product.id),
                "rating": 6,
                "comment": "Invalid rating",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

    def test_invalid_target_id_fails(self):
        self.login_user()

        response = self.client.post(
            "/api/reviews/",
            {
                "target_type": "product",
                "target_id": "invalid-id",
                "rating": 5,
                "comment": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )
