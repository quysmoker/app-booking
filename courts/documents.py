

from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    FloatField,
    StringField,
)


class Court(Document):
    SPORT_TYPE_CHOICES = (
        "pickleball",
        "badminton",
        "tennis",
        "football",
    )

    STATUS_CHOICES = (
        "available",
        "maintenance",
        "unavailable",
    )

    name = StringField(
        required=True,
        max_length=100,
    )
    description = StringField()

    sport_type = StringField(
        required=True,
        choices=SPORT_TYPE_CHOICES,
        default="pickleball",
    )

    location = StringField(required=True)
    image = StringField()

    price_per_hour = FloatField(required=True)

    status = StringField(
        choices=STATUS_CHOICES,
        default="available",
    )

    is_active = BooleanField(default=True)

    created_at = DateTimeField(
        default=datetime.utcnow,
    )
    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "courts",
        "indexes": [
            "name",
            "sport_type",
            "location",
            "status",
            "is_active",
        ],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "sport_type": self.sport_type,
            "location": self.location,

            # Giữ address để tương thích frontend cũ.
            "address": self.location,

            "image": self.image,
            "price_per_hour": self.price_per_hour,
            "status": self.status,
            "is_active": self.is_active,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }
