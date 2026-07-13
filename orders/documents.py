from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentListField,
    FloatField,
    IntField,
    ReferenceField,
    StringField,
)

from users.documents import User


class OrderItem(EmbeddedDocument):
    # Lưu dạng snapshot để sản phẩm có thay đổi thì đơn cũ vẫn giữ nguyên
    product_id = StringField(required=True)
    product_name = StringField(required=True)
    product_image = StringField(default="")
    quantity = IntField(required=True, min_value=1)
    unit_price = FloatField(required=True, min_value=0)
    subtotal = FloatField(required=True, min_value=0)

    def to_json_data(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_image": self.product_image,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
        }


class Order(Document):
    STATUS_CHOICES = (
        "pending",
        "confirmed",
        "shipping",
        "completed",
        "cancelled",
    )

    PAYMENT_METHOD_CHOICES = (
        "cod",
        "bank_transfer",
        "vnpay",
        "momo",
    )

    PAYMENT_STATUS_CHOICES = (
        "unpaid",
        "paid",
        "refunded",
    )

    code = StringField(required=True, unique=True)
    user = ReferenceField(User, required=True)

    items = EmbeddedDocumentListField(
        OrderItem,
        required=True,
    )

    recipient_name = StringField(required=True)
    recipient_phone = StringField(required=True)
    shipping_address = StringField(required=True)
    note = StringField(default="")

    subtotal = FloatField(required=True, min_value=0)
    shipping_fee = FloatField(default=0, min_value=0)
    discount_amount = FloatField(default=0, min_value=0)
    total_amount = FloatField(required=True, min_value=0)

    status = StringField(
        choices=STATUS_CHOICES,
        default="pending",
    )

    payment_method = StringField(
        choices=PAYMENT_METHOD_CHOICES,
        default="cod",
    )

    payment_status = StringField(
        choices=PAYMENT_STATUS_CHOICES,
        default="unpaid",
    )

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    cancelled_at = DateTimeField()

    meta = {
        "collection": "orders",
        "indexes": [
            "code",
            "user",
            "status",
            "payment_status",
            "-created_at",
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "code": self.code,
            "user": (
                self.user.to_json_data()
                if self.user
                else None
            ),
            "items": [
                item.to_json_data()
                for item in self.items
            ],
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
            "shipping_address": self.shipping_address,
            "note": self.note,
            "subtotal": self.subtotal,
            "shipping_fee": self.shipping_fee,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "status": self.status,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
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
            "cancelled_at": (
                self.cancelled_at.isoformat()
                if self.cancelled_at
                else None
            ),
        }
