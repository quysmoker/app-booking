from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from notifications.documents import Notification
from notifications.services import (
    create_bulk_notifications,
    create_notification,
)
from users.documents import User


def get_notification_by_id(notification_id):
    if not ObjectId.is_valid(notification_id):
        return None

    return Notification.objects(
        id=ObjectId(notification_id)
    ).first()


def get_user_by_id(user_id):
    if not ObjectId.is_valid(user_id):
        return None

    return User.objects(
        id=ObjectId(user_id)
    ).first()


def is_admin_or_staff(user):
    return getattr(
        user,
        "role",
        "",
    ) in ["admin", "staff"]


def parse_boolean(value):
    if value is None:
        return None

    normalized_value = str(value).strip().lower()

    if normalized_value == "true":
        return True

    if normalized_value == "false":
        return False

    return None


class NotificationListView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        notifications = Notification.objects(
            recipient=user,
            is_active=True,
        )

        is_read = request.query_params.get(
            "is_read"
        )

        notification_type = (
            request.query_params.get(
                "notification_type"
            )
        )

        if is_read is not None:
            parsed_is_read = parse_boolean(is_read)

            if parsed_is_read is None:
                return Response(
                    {
                        "message": (
                            "is_read must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notifications = notifications.filter(
                is_read=parsed_is_read
            )

        if notification_type:
            if (
                notification_type
                not in Notification.TYPE_CHOICES
            ):
                return Response(
                    {
                        "message": (
                            "Invalid notification_type"
                        ),
                        "allowed_types": list(
                            Notification.TYPE_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notifications = notifications.filter(
                notification_type=notification_type
            )

        try:
            page = int(
                request.query_params.get(
                    "page",
                    1,
                )
            )

            page_size = int(
                request.query_params.get(
                    "page_size",
                    20,
                )
            )
        except (TypeError, ValueError):
            return Response(
                {
                    "message": (
                        "page and page_size must be integers"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        total = notifications.count()
        skip = (page - 1) * page_size

        paginated_notifications = (
            notifications
            .skip(skip)
            .limit(page_size)
        )

        unread_count = Notification.objects(
            recipient=user,
            is_active=True,
            is_read=False,
        ).count()

        return Response(
            {
                "message": (
                    "Get notifications successfully"
                ),
                "data": [
                    notification.to_json_data()
                    for notification
                    in paginated_notifications
                ],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (
                        (total + page_size - 1)
                        // page_size
                    ),
                },
                "unread_count": unread_count,
            },
            status=status.HTTP_200_OK,
        )


class NotificationDetailView(APIView):
    @login_required
    def get(
        self,
        request,
        notification_id,
    ):
        notification = get_notification_by_id(
            notification_id
        )

        if (
            not notification
            or not notification.is_active
        ):
            return Response(
                {
                    "message": (
                        "Notification not found"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            notification.recipient.id != user.id
            and not is_admin_or_staff(user)
        ):
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": (
                    "Get notification detail successfully"
                ),
                "data": notification.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def delete(
        self,
        request,
        notification_id,
    ):
        notification = get_notification_by_id(
            notification_id
        )

        if (
            not notification
            or not notification.is_active
        ):
            return Response(
                {
                    "message": (
                        "Notification not found"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            notification.recipient.id != user.id
            and not is_admin_or_staff(user)
        ):
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        notification.is_active = False
        notification.updated_at = datetime.utcnow()
        notification.save()

        return Response(
            {
                "message": (
                    "Delete notification successfully"
                )
            },
            status=status.HTTP_200_OK,
        )


class NotificationUnreadCountView(APIView):
    @login_required
    def get(self, request):
        unread_count = Notification.objects(
            recipient=request.current_user,
            is_active=True,
            is_read=False,
        ).count()

        return Response(
            {
                "message": (
                    "Get unread count successfully"
                ),
                "data": {
                    "unread_count": unread_count
                },
            },
            status=status.HTTP_200_OK,
        )


class NotificationMarkReadView(APIView):
    @login_required
    def patch(
        self,
        request,
        notification_id,
    ):
        notification = get_notification_by_id(
            notification_id
        )

        if (
            not notification
            or not notification.is_active
        ):
            return Response(
                {
                    "message": (
                        "Notification not found"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if notification.recipient.id != user.id:
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            notification.updated_at = (
                datetime.utcnow()
            )
            notification.save()

        return Response(
            {
                "message": (
                    "Mark notification as read successfully"
                ),
                "data": notification.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class NotificationMarkUnreadView(APIView):
    @login_required
    def patch(
        self,
        request,
        notification_id,
    ):
        notification = get_notification_by_id(
            notification_id
        )

        if (
            not notification
            or not notification.is_active
        ):
            return Response(
                {
                    "message": (
                        "Notification not found"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if notification.recipient.id != user.id:
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        notification.is_read = False
        notification.read_at = None
        notification.updated_at = datetime.utcnow()
        notification.save()

        return Response(
            {
                "message": (
                    "Mark notification as unread successfully"
                ),
                "data": notification.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class NotificationMarkAllReadView(APIView):
    @login_required
    def patch(self, request):
        now = datetime.utcnow()

        notifications = Notification.objects(
            recipient=request.current_user,
            is_active=True,
            is_read=False,
        )

        updated_count = notifications.count()

        notifications.update(
            set__is_read=True,
            set__read_at=now,
            set__updated_at=now,
        )

        return Response(
            {
                "message": (
                    "Mark all notifications as read "
                    "successfully"
                ),
                "data": {
                    "updated_count": updated_count
                },
            },
            status=status.HTTP_200_OK,
        )


class AdminNotificationCreateView(APIView):
    @login_required
    def post(self, request):
        admin_user = request.current_user

        if not is_admin_or_staff(admin_user):
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        recipient_id = data.get(
            "recipient_id"
        )

        title = str(
            data.get(
                "title",
                "",
            )
        ).strip()

        message = str(
            data.get(
                "message",
                "",
            )
        ).strip()

        notification_type = data.get(
            "notification_type",
            "system",
        )

        related_id = str(
            data.get(
                "related_id",
                "",
            )
        ).strip()

        related_type = str(
            data.get(
                "related_type",
                "",
            )
        ).strip()

        custom_data = data.get(
            "data",
            {},
        )

        if not recipient_id:
            return Response(
                {
                    "message": (
                        "recipient_id is required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not title or not message:
            return Response(
                {
                    "message": (
                        "title and message are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(title) > 255:
            return Response(
                {
                    "message": (
                        "title cannot exceed 255 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(message) > 2000:
            return Response(
                {
                    "message": (
                        "message cannot exceed "
                        "2000 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            notification_type
            not in Notification.TYPE_CHOICES
        ):
            return Response(
                {
                    "message": (
                        "Invalid notification_type"
                    ),
                    "allowed_types": list(
                        Notification.TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(custom_data, dict):
            return Response(
                {
                    "message": "data must be an object"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient = get_user_by_id(
            recipient_id
        )

        if not recipient:
            return Response(
                {
                    "message": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        notification = create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type,
            data=custom_data,
        )

        return Response(
            {
                "message": (
                    "Create notification successfully"
                ),
                "data": notification.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class AdminBroadcastNotificationView(APIView):
    @login_required
    def post(self, request):
        admin_user = request.current_user

        if not is_admin_or_staff(admin_user):
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        title = str(
            data.get(
                "title",
                "",
            )
        ).strip()

        message = str(
            data.get(
                "message",
                "",
            )
        ).strip()

        notification_type = data.get(
            "notification_type",
            "system",
        )

        related_id = str(
            data.get(
                "related_id",
                "",
            )
        ).strip()

        related_type = str(
            data.get(
                "related_type",
                "",
            )
        ).strip()

        custom_data = data.get(
            "data",
            {},
        )

        if not title or not message:
            return Response(
                {
                    "message": (
                        "title and message are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            notification_type
            not in Notification.TYPE_CHOICES
        ):
            return Response(
                {
                    "message": (
                        "Invalid notification_type"
                    ),
                    "allowed_types": list(
                        Notification.TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(custom_data, dict):
            return Response(
                {
                    "message": "data must be an object"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipients = User.objects()

        notifications = create_bulk_notifications(
            recipients=recipients,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type,
            data=custom_data,
        )

        return Response(
            {
                "message": (
                    "Broadcast notification successfully"
                ),
                "data": {
                    "sent_count": len(
                        notifications
                    )
                },
            },
            status=status.HTTP_201_CREATED,
        )


class AdminNotificationListView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user

        if not is_admin_or_staff(user):
            return Response(
                {
                    "message": "Permission denied"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        notifications = Notification.objects()

        recipient_id = request.query_params.get(
            "recipient_id"
        )

        is_read = request.query_params.get(
            "is_read"
        )

        is_active = request.query_params.get(
            "is_active"
        )

        notification_type = (
            request.query_params.get(
                "notification_type"
            )
        )

        if recipient_id:
            recipient = get_user_by_id(
                recipient_id
            )

            if not recipient:
                return Response(
                    {
                        "message": "User not found"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            notifications = notifications.filter(
                recipient=recipient
            )

        if is_read is not None:
            parsed_is_read = parse_boolean(is_read)

            if parsed_is_read is None:
                return Response(
                    {
                        "message": (
                            "is_read must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notifications = notifications.filter(
                is_read=parsed_is_read
            )

        if is_active is not None:
            parsed_is_active = parse_boolean(
                is_active
            )

            if parsed_is_active is None:
                return Response(
                    {
                        "message": (
                            "is_active must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notifications = notifications.filter(
                is_active=parsed_is_active
            )

        if notification_type:
            if (
                notification_type
                not in Notification.TYPE_CHOICES
            ):
                return Response(
                    {
                        "message": (
                            "Invalid notification_type"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notifications = notifications.filter(
                notification_type=notification_type
            )

        return Response(
            {
                "message": (
                    "Get all notifications successfully"
                ),
                "data": [
                    notification.to_json_data()
                    for notification in notifications
                ],
            },
            status=status.HTTP_200_OK,
        )
