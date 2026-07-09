from mongoengine import Document, ReferenceField, DateTimeField, StringField, FloatField
from datetime import datetime
from users.documents import User
from courts.documents import Court


class Booking(Document):
    STATUS_CHOICES = ("pending", "confirmed", "cancelled", "completed")

    user = ReferenceField(User, required=True)
    court = ReferenceField(Court, required=True)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)
    total_price = FloatField(required=True)
    status = StringField(choices=STATUS_CHOICES, default="pending")
    note = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "bookings",
        "indexes": ["user", "court", "status", "start_time"],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "user": self.user.to_json_data() if self.user else None,
            "court": self.court.to_json_data() if self.court else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_price": self.total_price,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
