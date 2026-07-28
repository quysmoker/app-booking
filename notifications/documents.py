from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    ReferenceField,
    StringField,
)

from users.documents import User


class Notification(Document):
    TYPE_CHOICES = (
        "system",
        "booking",
        "order",
        "payment",
        "voucher",
        "review",
    )

    recipient = ReferenceField(
        User,
        required=True,
    )

    notification_type = StringField(
        required=True,
        choices=TYPE_CHOICES,
        default="system",
    )

    title = StringField(
        required=True,
        max_length=255,
    )

    message = StringField(
        required=True,
        max_length=2000,
    )

    related_id = StringField(
        default="",
    )

    related_type = StringField(
        default="",
    )

    data = DictField(
        default=dict,
    )

    is_read = BooleanField(
        default=False,
    )

    is_active = BooleanField(
        default=True,
    )

    read_at = DateTimeField(
        null=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "notifications",
        "indexes": [
            "recipient",
            "notification_type",
            "related_id",
            "is_read",
            "is_active",
            "-created_at",
            {
                "fields": [
                    "recipient",
                    "is_read",
                    "is_active",
                ]
            },
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "recipient": {
                "id": str(self.recipient.id),
                "email": getattr(
                    self.recipient,
                    "email",
                    "",
                ),
                "full_name": getattr(
                    self.recipient,
                    "full_name",
                    "",
                ),
            }
            if self.recipient
            else None,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "related_id": self.related_id,
            "related_type": self.related_type,
            "data": self.data or {},
            "is_read": self.is_read,
            "is_active": self.is_active,
            "read_at": (
                self.read_at.isoformat()
                if self.read_at
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
