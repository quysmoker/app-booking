from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime


class User(Document):
    ROLE_CHOICES = ("admin", "staff", "user")

    full_name = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True)
    phone = StringField(max_length=20)
    password = StringField(required=True)
    role = StringField(choices=ROLE_CHOICES, default="user")
    avatar = StringField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "users",
        "indexes": ["email", "role"],
        "ordering": ["-created_at"],
    }

    def to_json_data(self):
        return {
            "id": str(self.id),
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
