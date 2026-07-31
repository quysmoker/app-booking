from django.urls import path

from notifications.views import (
    AdminBroadcastNotificationView,
    AdminNotificationCreateView,
    AdminNotificationListView,
    AdminNotificationStatusUpdateView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationMarkUnreadView,
    NotificationUnreadCountView,
)


urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="notification-mark-all-read",
    ),
    path(
        "admin/all/",
        AdminNotificationListView.as_view(),
        name="admin-notification-list",
    ),
    path(
        "admin/create/",
        AdminNotificationCreateView.as_view(),
        name="admin-notification-create",
    ),
    path(
        "admin/broadcast/",
        AdminBroadcastNotificationView.as_view(),
        name="admin-notification-broadcast",
    ),
    path(
        "<str:notification_id>/status/",
        AdminNotificationStatusUpdateView.as_view(),
        name="admin-notification-status-update",
    ),
    path(
        "<str:notification_id>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "<str:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
    path(
        "<str:notification_id>/unread/",
        NotificationMarkUnreadView.as_view(),
        name="notification-mark-unread",
    ),
]
