from django.urls import path

from reviews.views import (
    AdminReviewListView,
    MyReviewListView,
    ReviewDetailView,
    ReviewListCreateView,
    ReviewSummaryView,
)


urlpatterns = [
    path(
        "",
        ReviewListCreateView.as_view(),
        name="review-list-create",
    ),
    path(
        "summary/",
        ReviewSummaryView.as_view(),
        name="review-summary",
    ),
    path(
        "my-reviews/",
        MyReviewListView.as_view(),
        name="my-review-list",
    ),
    path(
        "admin/all/",
        AdminReviewListView.as_view(),
        name="admin-review-list",
    ),
    path(
        "<str:review_id>/",
        ReviewDetailView.as_view(),
        name="review-detail",
    ),
]
