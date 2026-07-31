from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from mongoengine.queryset.visitor import Q

from authentication.permissions import (
    get_current_user,
    role_required,
)
from vouchers.documents import Voucher


def get_voucher_by_id(voucher_id):
    try:
        return Voucher.objects(
            id=ObjectId(voucher_id)
        ).first()
    except Exception:
        return None


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value):
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_boolean(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.strip().lower()

        if value == "true":
            return True

        if value == "false":
            return False

    return None


class VoucherListCreateView(APIView):
    def get(self, request):
        current_user = get_current_user(request)

        is_manager = (
            current_user is not None
            and current_user.role
            in ["admin", "staff"]
        )

        if is_manager:
            vouchers = Voucher.objects()

            search = str(
                request.query_params.get(
                    "search",
                    "",
                )
            ).strip()

            discount_type = (
                request.query_params.get(
                    "discount_type"
                )
            )

            is_active = (
                request.query_params.get(
                    "is_active"
                )
            )

            if discount_type:
                if (
                    discount_type
                    not in (
                        Voucher
                        .DISCOUNT_TYPE_CHOICES
                    )
                ):
                    return Response(
                        {
                            "message": (
                                "Invalid discount type"
                            ),
                            "allowed_types": list(
                                Voucher
                                .DISCOUNT_TYPE_CHOICES
                            ),
                        },
                        status=(
                            status
                            .HTTP_400_BAD_REQUEST
                        ),
                    )

                vouchers = vouchers.filter(
                    discount_type=discount_type
                )

            if is_active is not None:
                active_value = parse_boolean(
                    is_active
                )

                if active_value is None:
                    return Response(
                        {
                            "message": (
                                "is_active must be "
                                "true or false"
                            )
                        },
                        status=(
                            status
                            .HTTP_400_BAD_REQUEST
                        ),
                    )

                vouchers = vouchers.filter(
                    is_active=active_value
                )

            if search:
                vouchers = vouchers.filter(
                    Q(code__icontains=search)
                    | Q(name__icontains=search)
                    | Q(
                        description__icontains=search
                    )
                )

            voucher_data = [
                voucher.to_json_data()
                for voucher in vouchers
            ]

        else:
            now = datetime.utcnow()

            vouchers = Voucher.objects(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now,
            )

            voucher_data = [
                voucher.to_json_data()
                for voucher in vouchers
                if voucher.is_available()
            ]

        return Response(
            {
                "message": (
                    "Get vouchers successfully"
                ),
                "total": len(voucher_data),
                "data": voucher_data,
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def post(self, request):
        data = request.data

        code = data.get("code")
        name = data.get("name")
        discount_type = data.get("discount_type")
        discount_value = parse_float(
            data.get("discount_value")
        )
        min_order_value = parse_float(
            data.get("min_order_value", 0)
        )
        start_date = parse_datetime(
            data.get("start_date")
        )
        end_date = parse_datetime(
            data.get("end_date")
        )

        if (
            not code
            or not name
            or not discount_type
            or discount_value is None
            or not start_date
            or not end_date
        ):
            return Response(
                {
                    "message": (
                        "code, name, discount_type, "
                        "discount_value, start_date and "
                        "end_date are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = code.strip().upper()

        if Voucher.objects(code=code).first():
            return Response(
                {"message": "Voucher code already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if discount_type not in Voucher.DISCOUNT_TYPE_CHOICES:
            return Response(
                {
                    "message": "Invalid discount type",
                    "allowed_types": list(
                        Voucher.DISCOUNT_TYPE_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if discount_value <= 0:
            return Response(
                {
                    "message": (
                        "discount_value must be greater than 0"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            discount_type == "percentage"
            and discount_value > 100
        ):
            return Response(
                {
                    "message": (
                        "Percentage discount cannot exceed 100"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if min_order_value is None or min_order_value < 0:
            return Response(
                {
                    "message": (
                        "min_order_value must be non-negative"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_date >= end_date:
            return Response(
                {
                    "message": (
                        "start_date must be before end_date"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_discount = data.get("max_discount")

        if max_discount is not None:
            max_discount = parse_float(max_discount)

            if max_discount is None or max_discount < 0:
                return Response(
                    {
                        "message": (
                            "max_discount must be non-negative"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        usage_limit = data.get("usage_limit")

        if usage_limit is not None:
            usage_limit = parse_int(usage_limit)

            if usage_limit is None or usage_limit < 1:
                return Response(
                    {
                        "message": (
                            "usage_limit must be greater than 0"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        voucher = Voucher(
            code=code,
            name=name.strip(),
            description=data.get("description", ""),
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_value=min_order_value,
            max_discount=max_discount,
            start_date=start_date,
            end_date=end_date,
            usage_limit=usage_limit,
            used_count=0,
            is_active=True,
        )
        voucher.save()

        return Response(
            {
                "message": "Create voucher successfully",
                "data": voucher.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class VoucherDetailView(APIView):
    def get(self, request, voucher_id):
        voucher = get_voucher_by_id(voucher_id)

        if not voucher:
            return Response(
                {"message": "Voucher not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_user = get_current_user(
            request
        )

        is_manager = (
            current_user is not None
            and current_user.role
            in ["admin", "staff"]
        )

        if (
            not is_manager
            and not voucher.is_available()
        ):
            return Response(
                {"message": "Voucher not found"},
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )
        return Response(
            {
                "message": "Get voucher detail successfully",
                "data": voucher.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def put(self, request, voucher_id):
        voucher = get_voucher_by_id(voucher_id)

        if not voucher:
            return Response(
                {"message": "Voucher not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data

        if data.get("name") is not None:
            name = str(data.get("name")).strip()

            if not name:
                return Response(
                    {"message": "name cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.name = name

        if data.get("description") is not None:
            voucher.description = data.get("description")

        if data.get("discount_type") is not None:
            discount_type = data.get("discount_type")

            if discount_type not in Voucher.DISCOUNT_TYPE_CHOICES:
                return Response(
                    {"message": "Invalid discount type"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.discount_type = discount_type

        if data.get("discount_value") is not None:
            discount_value = parse_float(
                data.get("discount_value")
            )

            if discount_value is None or discount_value <= 0:
                return Response(
                    {
                        "message": (
                            "discount_value must be greater than 0"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                voucher.discount_type == "percentage"
                and discount_value > 100
            ):
                return Response(
                    {
                        "message": (
                            "Percentage discount cannot exceed 100"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.discount_value = discount_value

        if data.get("min_order_value") is not None:
            min_order_value = parse_float(
                data.get("min_order_value")
            )

            if (
                min_order_value is None
                or min_order_value < 0
            ):
                return Response(
                    {
                        "message": (
                            "min_order_value must be non-negative"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.min_order_value = min_order_value

        if data.get("max_discount") is not None:
            max_discount = parse_float(
                data.get("max_discount")
            )

            if max_discount is None or max_discount < 0:
                return Response(
                    {
                        "message": (
                            "max_discount must be non-negative"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.max_discount = max_discount

        if data.get("usage_limit") is not None:
            usage_limit = parse_int(
                data.get("usage_limit")
            )

            if usage_limit is None or usage_limit < 1:
                return Response(
                    {
                        "message": (
                            "usage_limit must be greater than 0"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.usage_limit = usage_limit

        if data.get("start_date") is not None:
            start_date = parse_datetime(
                data.get("start_date")
            )

            if not start_date:
                return Response(
                    {"message": "Invalid start_date"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.start_date = start_date

        if data.get("end_date") is not None:
            end_date = parse_datetime(
                data.get("end_date")
            )

            if not end_date:
                return Response(
                    {"message": "Invalid end_date"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.end_date = end_date

        if voucher.start_date >= voucher.end_date:
            return Response(
                {
                    "message": (
                        "start_date must be before end_date"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data.get("is_active") is not None:
            is_active = parse_boolean(
                data.get("is_active")
            )

            if is_active is None:
                return Response(
                    {
                        "message": (
                            "is_active must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher.is_active = is_active

        voucher.updated_at = datetime.utcnow()
        voucher.save()

        return Response(
            {
                "message": "Update voucher successfully",
                "data": voucher.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def delete(self, request, voucher_id):
        voucher = get_voucher_by_id(voucher_id)

        if not voucher:
            return Response(
                {"message": "Voucher not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        voucher.is_active = False
        voucher.updated_at = datetime.utcnow()
        voucher.save()

        return Response(
            {"message": "Delete voucher successfully"},
            status=status.HTTP_200_OK,
        )

class VoucherStatusUpdateView(APIView):
    @role_required(["admin", "staff"])
    def patch(self, request, voucher_id):
        voucher = get_voucher_by_id(
            voucher_id
        )

        if not voucher:
            return Response(
                {"message": "Voucher not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        active_value = parse_boolean(
            request.data.get("is_active")
        )

        if active_value is None:
            return Response(
                {
                    "message": (
                        "is_active must be "
                        "true or false"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        voucher.is_active = active_value
        voucher.updated_at = datetime.utcnow()
        voucher.save()

        return Response(
            {
                "message": (
                    "Update voucher status successfully"
                ),
                "data": voucher.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )



class VoucherValidateView(APIView):
    def post(self, request):
        code = request.data.get("code")
        order_amount = parse_float(
            request.data.get("order_amount")
        )

        if not code or order_amount is None:
            return Response(
                {
                    "message": (
                        "code and order_amount are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order_amount < 0:
            return Response(
                {
                    "message": (
                        "order_amount must be non-negative"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        voucher = Voucher.objects(
            code=code.strip().upper()
        ).first()

        if not voucher:
            return Response(
                {"message": "Voucher not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not voucher.is_available():
            return Response(
                {
                    "message": (
                        "Voucher is expired, inactive "
                        "or has reached usage limit"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order_amount < voucher.min_order_value:
            return Response(
                {
                    "message": (
                        "Order amount does not meet "
                        "minimum requirement"
                    ),
                    "min_order_value": (
                        voucher.min_order_value
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        discount_amount = voucher.calculate_discount(
            order_amount
        )

        final_amount = max(
            order_amount - discount_amount,
            0,
        )

        return Response(
            {
                "message": "Voucher is valid",
                "data": {
                    "voucher": voucher.to_json_data(),
                    "order_amount": order_amount,
                    "discount_amount": discount_amount,
                    "final_amount": final_amount,
                },
            },
            status=status.HTTP_200_OK,
        )
