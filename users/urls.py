from django.urls import path

from users.views import (
    UserDetailView,
    UserListCreateView,
    UserStatusUpdateView,
)


urlpatterns = [
    path(
        "",
        UserListCreateView.as_view(),
        name="user-list-create",
    ),
    path(
        "<str:user_id>/status/",
        UserStatusUpdateView.as_view(),
        name="user-status-update",
    ),
    path(
        "<str:user_id>/",
        UserDetailView.as_view(),
        name="user-detail",
    ),
]
