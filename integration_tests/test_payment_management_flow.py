from bson import ObjectId

from integration_tests.base import IntegrationTestBase
from notifications.documents import Notification
from orders.documents import Order, OrderItem
from payments.documents import Payment


class PaymentManagementIntegrationTest(
    IntegrationTestBase
):
    def setUp(self):
        super().setUp()

        Notification.drop_collection()
        Payment.drop_collection()
        Order.drop_collection()

        self.order = Order(
            code="ORD-PAYMENT-001",
            user=self.user,
            items=[
                OrderItem(
                    product_id=str(ObjectId()),
                    product_name="Payment Test Product",
                    quantity=1,
                    unit_price=500000,
                    subtotal=500000,
                )
            ],
            recipient_name="Integration User",
            recipient_phone="0900000000",
            shipping_address="Payment Test Address",
            subtotal=500000,
            shipping_fee=0,
            discount_amount=0,
            total_amount=500000,
            status="pending",
            payment_method="bank_transfer",
            payment_status="unpaid",
        ).save()

        self.payment = Payment(
            order=self.order,
            user=self.user,
            amount=self.order.total_amount,
            method="bank_transfer",
            status="pending",
        ).save()

    def tearDown(self):
        Notification.drop_collection()
        Payment.drop_collection()
        Order.drop_collection()
        super().tearDown()

    def test_user_cannot_confirm_payment(self):
        self.login_user()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/confirm/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    def test_admin_can_search_and_filter_payments(self):
        self.login_admin()

        response = self.client.get(
            "/api/payments/",
            {
                "search": "user@test.com",
                "status": "pending",
                "method": "bank_transfer",
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
            response.data["data"][0]["order_code"],
            self.order.code,
        )
        self.assertEqual(
            response.data["data"][0]["user"]["email"],
            self.user.email,
        )

    def test_admin_can_confirm_payment(self):
        self.login_admin()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/confirm/",
            {"transaction_code": "BANK-TEST-001"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.payment.reload()
        self.order.reload()

        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(
            self.payment.transaction_code,
            "BANK-TEST-001",
        )
        self.assertEqual(
            self.order.payment_status,
            "paid",
        )
        self.assertTrue(
            Notification.objects(
                recipient=self.user,
                notification_type="payment",
            ).count()
            > 0
        )

    def test_admin_can_mark_pending_payment_failed(self):
        self.login_admin()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/fail/",
            {"failure_reason": "Sai nội dung chuyển khoản"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.payment.reload()

        self.assertEqual(self.payment.status, "failed")
        self.assertEqual(
            self.payment.failure_reason,
            "Sai nội dung chuyển khoản",
        )

    def test_admin_can_refund_paid_payment(self):
        self.payment.status = "paid"
        self.payment.transaction_code = "BANK-PAID-001"
        self.payment.save()

        self.order.payment_status = "paid"
        self.order.save()

        self.login_admin()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/refund/",
            {"refund_reason": "Khách hàng hủy đơn"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        self.payment.reload()
        self.order.reload()

        self.assertEqual(self.payment.status, "refunded")
        self.assertEqual(
            self.order.payment_status,
            "refunded",
        )
        self.assertIsNotNone(self.payment.refunded_at)
        self.assertEqual(
            self.payment.refund_reason,
            "Khách hàng hủy đơn",
        )

    def test_pending_payment_cannot_be_refunded(self):
        self.login_admin()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/refund/",
            {"refund_reason": "Invalid refund"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

    def test_cancelled_order_payment_cannot_be_confirmed(self):
        self.order.status = "cancelled"
        self.order.save()

        self.login_admin()

        response = self.client.put(
            f"/api/payments/{self.payment.id}/confirm/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )
