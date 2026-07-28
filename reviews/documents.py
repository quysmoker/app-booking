from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ReferenceField,
    StringField,
)

from users.documents import User


class Review(Document):
    TARGET_TYPE_CHOICES = (
        "product",
        "court",
    )

    user = ReferenceField(
        User,
        required=True,
    )

    target_type = StringField(
        required=True,
        choices=TARGET_TYPE_CHOICES,
    )

    target_id = StringField(
        required=True,
    )

    rating = IntField(
        required=True,
        min_value=1,
        max_value=5,
    )

    comment = StringField(
        default="",
        max_length=2000,
    )

    is_active = BooleanField(
        default=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "reviews",
        "indexes": [
            "user",
            "target_type",
            "target_id",
            "rating",
            "is_active",
            "-created_at",
            {
                "fields": [
                    "user",
                    "target_type",
                    "target_id",
                ],
                "unique": True,
            },
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "user": (
                self.user.to_json_data()
                if self.user
                else None
            ),
            "target_type": self.target_type,
            "target_id": self.target_id,
            "rating": self.rating,
            "comment": self.comment,
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
