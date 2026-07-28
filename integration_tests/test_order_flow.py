from integration_tests.base import IntegrationTestBase
from carts.documents import Cart
from notifications.documents import Notification
from orders.documents import Order
from products.documents import Product
from vouchers.documents import Voucher


class OrderIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Product.drop_collection()
        Cart.drop_collection()
        Order.drop_collection()
        Voucher.drop_collection()
        Notification.drop_collection()

        self.product = Product(
            name="Integration Pickleball Paddle",
            price=500000,
            stock=10,
            is_active=True,
        ).save()

    def tearDown(self):
        Notification.drop_collection()
        Voucher.drop_collection()
        Order.drop_collection()
        Cart.drop_collection()
        Product.drop_collection()

        super().tearDown()

    def test_create_order_reduces_product_stock(self):
        self.login_user()

        initial_stock = self.product.stock

        response = self.client.post(
            "/api/orders/",
            {
                "items": [
                    {
                        "product_id": str(
                            self.product.id
                        ),
                        "quantity": 2,
                    }
                ],
                "shipping_address": (
                    "123 Integration Test Street"
                ),
                "payment_method": "cod",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [200, 201],
            response.data,
        )

        self.product.reload()

        self.assertEqual(
            self.product.stock,
            initial_stock - 2,
        )

        order = Order.objects(
            user=self.user
        ).first()

        self.assertIsNotNone(order)

    def test_create_order_creates_notification(self):
        self.login_user()

        response = self.client.post(
            "/api/orders/",
            {
                "items": [
                    {
                        "product_id": str(
                            self.product.id
                        ),
                        "quantity": 1,
                    }
                ],
                "shipping_address": (
                    "123 Integration Test Street"
                ),
                "payment_method": "cod",
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
            notification_type="order",
        ).first()

        self.assertIsNotNone(notification)

    def test_order_fails_when_stock_is_insufficient(self):
        self.login_user()

        response = self.client.post(
            "/api/orders/",
            {
                "items": [
                    {
                        "product_id": str(
                            self.product.id
                        ),
                        "quantity": 1000,
                    }
                ],
                "shipping_address": (
                    "123 Integration Test Street"
                ),
                "payment_method": "cod",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [400, 409],
            response.data,
        )

        self.product.reload()

        self.assertEqual(
            self.product.stock,
            10,
        )
