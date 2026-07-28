from notifications.documents import Notification


def create_notification(
    recipient,
    title,
    message,
    notification_type="system",
    related_id="",
    related_type="",
    data=None,
):
    if recipient is None:
        return None

    if notification_type not in Notification.TYPE_CHOICES:
        notification_type = "system"

    notification = Notification(
        recipient=recipient,
        notification_type=notification_type,
        title=str(title).strip(),
        message=str(message).strip(),
        related_id=(
            str(related_id)
            if related_id
            else ""
        ),
        related_type=(
            str(related_type).strip()
            if related_type
            else ""
        ),
        data=data or {},
    )

    notification.save()

    return notification


def create_bulk_notifications(
    recipients,
    title,
    message,
    notification_type="system",
    related_id="",
    related_type="",
    data=None,
):
    notifications = []

    for recipient in recipients:
        notification = create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type,
            data=data,
        )

        if notification:
            notifications.append(notification)

    return notifications
