from datetime import datetime

from mongoengine import (
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    IntField,
    FloatField,
    ReferenceField,
    DateTimeField,
)

from users.documents import User
from products.documents import Product


class CartItem(EmbeddedDocument):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = IntField(
        required=True,
        min_value=1,
        default=1,
    )

    # Giá sản phẩm tại thời điểm thêm/cập nhật giỏ hàng
    unit_price = FloatField(
        required=True,
        min_value=0,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    def get_subtotal(self):
        return self.unit_price * self.quantity

    def to_json_data(self):
        return {
            "product": (
                self.product.to_json_data()
                if self.product
                else None
            ),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.get_subtotal(),
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


class Cart(Document):
    user = ReferenceField(
        User,
        required=True,
        unique=True,
    )

    items = EmbeddedDocumentListField(
        CartItem,
        default=list,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "carts",
        "indexes": [
            {
                "fields": ["user"],
                "unique": True,
            }
        ],
    }

    def get_total_quantity(self):
        return sum(
            item.quantity
            for item in self.items
        )

    def get_total_price(self):
        return sum(
            item.get_subtotal()
            for item in self.items
        )

    def to_json_data(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user.id),
            "items": [
                item.to_json_data()
                for item in self.items
                if item.product
            ],
            "total_quantity": self.get_total_quantity(),
            "total_price": self.get_total_price(),
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
