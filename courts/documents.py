from mongoengine import Document, StringField, FloatField, BooleanField, DateTimeField
from datetime import datetime


class Court(Document):
    name = StringField(required=True, max_length=100)
    description = StringField()
    location = StringField(required=True)
    image = StringField()
    price_per_hour = FloatField(required=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "courts",
        "indexes": ["name", "location", "is_active"],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "image": self.image,
            "price_per_hour": self.price_per_hour,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
