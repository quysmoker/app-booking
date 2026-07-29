from collections import defaultdict
from datetime import datetime, timedelta


def is_admin_or_staff(user):
    return getattr(user, "role", "") in [
        "admin",
        "staff",
    ]


def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        )
    except (TypeError, ValueError):
        return None


def get_date_range(request):
    start_date_value = request.query_params.get(
        "start_date"
    )
    end_date_value = request.query_params.get(
        "end_date"
    )

    start_date = parse_date(start_date_value)
    end_date = parse_date(end_date_value)

    if start_date_value and not start_date:
        return (
            None,
            None,
            "start_date must have format YYYY-MM-DD",
        )

    if end_date_value and not end_date:
        return (
            None,
            None,
            "end_date must have format YYYY-MM-DD",
        )

    if start_date and end_date:
        if start_date > end_date:
            return (
                None,
                None,
                "start_date cannot be greater than end_date",
            )

    if end_date:
        end_date = end_date + timedelta(days=1)

    return start_date, end_date, None


def filter_queryset_by_date(
    queryset,
    start_date=None,
    end_date=None,
    field_name="created_at",
):
    filters = {}

    if start_date:
        filters[f"{field_name}__gte"] = start_date

    if end_date:
        filters[f"{field_name}__lt"] = end_date

    if filters:
        queryset = queryset.filter(**filters)

    return queryset


def get_numeric_value(
    obj,
    field_names,
    default=0,
):
    for field_name in field_names:
        value = getattr(
            obj,
            field_name,
            None,
        )

        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    return float(default)


def serialize_document(document):
    if document is None:
        return None

    if hasattr(document, "to_json_data"):
        return document.to_json_data()

    return {
        "id": str(document.id),
    }


def calculate_daily_revenue(
    documents,
    amount_fields,
    date_field="created_at",
):
    revenue_by_date = defaultdict(float)

    for document in documents:
        document_date = getattr(
            document,
            date_field,
            None,
        )

        if not document_date:
            continue

        date_key = document_date.strftime(
            "%Y-%m-%d"
        )

        amount = get_numeric_value(
            document,
            amount_fields,
        )

        revenue_by_date[date_key] += amount

    return [
        {
            "date": date,
            "revenue": round(revenue, 2),
        }
        for date, revenue in sorted(
            revenue_by_date.items()
        )
    ]


def calculate_monthly_revenue(
    documents,
    amount_fields,
    date_field="created_at",
):
    revenue_by_month = defaultdict(float)

    for document in documents:
        document_date = getattr(
            document,
            date_field,
            None,
        )

        if not document_date:
            continue

        month_key = document_date.strftime(
            "%Y-%m"
        )

        amount = get_numeric_value(
            document,
            amount_fields,
        )

        revenue_by_month[month_key] += amount

    return [
        {
            "month": month,
            "revenue": round(revenue, 2),
        }
        for month, revenue in sorted(
            revenue_by_month.items()
        )
    ]
