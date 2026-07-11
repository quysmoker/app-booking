from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    FloatField,
    IntField,
    BooleanField,
    DateTimeField,
    ListField,
)


class Product(Document):
    CATEGORY_CHOICES = (
        "racket",
        "ball",
        "shoes",
        "clothes",
        "accessory",
        "other",
    )

    name = StringField(required=True, max_length=150)
    description = StringField(default="")
    category = StringField(
        required=True,
        choices=CATEGORY_CHOICES,
    )
    brand = StringField(default="", max_length=100)
    price = FloatField(required=True, min_value=0)
    stock = IntField(required=True, default=0, min_value=0)
    image = StringField(default="")
    images = ListField(StringField(), default=list)
    is_active = BooleanField(default=True)

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "products",
        "indexes": [
            "name",
            "category",
            "brand",
            "is_active",
            "-created_at",
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "price": self.price,
            "stock": self.stock,
            "image": self.image,
            "images": self.images,
            "is_active": self.is_active,
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
