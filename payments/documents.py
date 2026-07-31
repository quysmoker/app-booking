from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    FloatField,
    ReferenceField,
    StringField,
)

from orders.documents import Order
from users.documents import User


class Payment(Document):
    METHOD_CHOICES = (
        "cod",
        "bank_transfer",
        "vnpay",
        "momo",
    )

    STATUS_CHOICES = (
        "pending",
        "paid",
        "failed",
        "refunded",
    )

    order = ReferenceField(
        Order,
        required=True,
        unique=True,
    )

    user = ReferenceField(
        User,
        required=True,
    )

    amount = FloatField(
        required=True,
        min_value=0,
    )

    method = StringField(
        required=True,
        choices=METHOD_CHOICES,
    )

    status = StringField(
        choices=STATUS_CHOICES,
        default="pending",
    )

    transaction_code = StringField(
        default="",
    )

    failure_reason = StringField(
        default="",
    )

    refund_reason = StringField(
        default="",
    )

    paid_at = DateTimeField()
    refunded_at = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "payments",
        "indexes": [
            "order",
            "user",
            "status",
            "method",
            "-created_at",
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "order_id": str(self.order.id),
            "order_code": self.order.code,
            "user_id": str(self.user.id),
            "user": (
                self.user.to_json_data()
                if self.user
                else None
            ),
            "amount": self.amount,
            "method": self.method,
            "status": self.status,
            "transaction_code": self.transaction_code,
            "failure_reason": self.failure_reason,
            "refund_reason": self.refund_reason,
            "paid_at": (
                self.paid_at.isoformat()
                if self.paid_at
                else None
            ),
            "refunded_at": (
                self.refunded_at.isoformat()
                if self.refunded_at
                else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }
