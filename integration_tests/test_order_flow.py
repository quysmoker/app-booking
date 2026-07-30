from carts.documents import Cart, CartItem
from integration_tests.base import (
    IntegrationTestBase,
)
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
            category="racket",
            price=500000,
            stock=10,
            is_active=True,
        ).save()

    def prepare_cart(self, quantity):
        return Cart(
            user=self.user,
            items=[
                CartItem(
                    product=self.product,
                    quantity=quantity,
                    unit_price=self.product.price,
                )
            ],
        ).save()

    def tearDown(self):
        Notification.drop_collection()
        Voucher.drop_collection()
        Order.drop_collection()
        Cart.drop_collection()
        Product.drop_collection()

        super().tearDown()

    def test_create_order_reduces_product_stock(
        self,
    ):
        self.login_user()
        self.prepare_cart(quantity=2)

        initial_stock = self.product.stock

        response = self.client.post(
            "/api/orders/",
            {
                "recipient_name": "Integration User",
                "recipient_phone": "0900000000",
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

    def test_create_order_creates_notification(
        self,
    ):
        self.login_user()
        self.prepare_cart(quantity=1)

        response = self.client.post(
            "/api/orders/",
            {
                "recipient_name": "Integration User",
                "recipient_phone": "0900000000",
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

    def test_order_fails_when_stock_is_insufficient(
        self,
    ):
        self.login_user()
        self.prepare_cart(quantity=1000)

        response = self.client.post(
            "/api/orders/",
            {
                "recipient_name": "Integration User",
                "recipient_phone": "0900000000",
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
