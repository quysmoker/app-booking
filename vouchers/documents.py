from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    FloatField,
    IntField,
    StringField,
)


class Voucher(Document):
    DISCOUNT_TYPE_CHOICES = (
        "percentage",
        "fixed",
    )

    code = StringField(
        required=True,
        unique=True,
        max_length=50,
    )

    name = StringField(
        required=True,
        max_length=150,
    )

    description = StringField(default="")

    discount_type = StringField(
        required=True,
        choices=DISCOUNT_TYPE_CHOICES,
    )

    discount_value = FloatField(
        required=True,
        min_value=0,
    )

    min_order_value = FloatField(
        default=0,
        min_value=0,
    )

    max_discount = FloatField(
        min_value=0,
        null=True,
    )

    start_date = DateTimeField(required=True)
    end_date = DateTimeField(required=True)

    usage_limit = IntField(
        min_value=1,
        null=True,
    )

    used_count = IntField(
        default=0,
        min_value=0,
    )

    is_active = BooleanField(default=True)

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "vouchers",
        "indexes": [
            "code",
            "discount_type",
            "is_active",
            "start_date",
            "end_date",
            "-created_at",
        ],
        "ordering": ["-created_at"],
    }

    def calculate_discount(self, order_amount):
        if self.discount_type == "percentage":
            discount = order_amount * self.discount_value / 100

            if self.max_discount is not None:
                discount = min(discount, self.max_discount)

            return discount

        return min(self.discount_value, order_amount)

    def is_available(self):
        now = datetime.utcnow()

        if not self.is_active:
            return False

        if now < self.start_date or now > self.end_date:
            return False

        if (
            self.usage_limit is not None
            and self.used_count >= self.usage_limit
        ):
            return False

        return True

    def to_json_data(self):
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": self.discount_value,
            "min_order_value": self.min_order_value,
            "max_discount": self.max_discount,
            "start_date": (
                self.start_date.isoformat()
                if self.start_date
                else None
            ),
            "end_date": (
                self.end_date.isoformat()
                if self.end_date
                else None
            ),
            "usage_limit": self.usage_limit,
            "used_count": self.used_count,
            "is_active": self.is_active,
            "is_available": self.is_available(),
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
