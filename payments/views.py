import uuid
from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from orders.documents import Order
from payments.documents import Payment


def get_payment_by_id(payment_id):
    try:
        return Payment.objects(
            id=ObjectId(payment_id)
        ).first()
    except Exception:
        return None


def get_order_by_id(order_id):
    try:
        return Order.objects(
            id=ObjectId(order_id)
        ).first()
    except Exception:
        return None


def generate_transaction_code(method):
    return (
        f"{method.upper()}-"
        f"{uuid.uuid4().hex[:12].upper()}"
    )


class PaymentListCreateView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user
        payment_status = request.query_params.get("status")
        method = request.query_params.get("method")

        if user.role in ["admin", "staff"]:
            payments = Payment.objects()
        else:
            payments = Payment.objects(user=user)

        if payment_status:
            if payment_status not in Payment.STATUS_CHOICES:
                return Response(
                    {
                        "message": "Invalid payment status",
                        "allowed_statuses": list(
                            Payment.STATUS_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payments = payments.filter(
                status=payment_status
            )

        if method:
            if method not in Payment.METHOD_CHOICES:
                return Response(
                    {
                        "message": "Invalid payment method",
                        "allowed_methods": list(
                            Payment.METHOD_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payments = payments.filter(
                method=method
            )

        return Response(
            {
                "message": "Get payments successfully",
                "data": [
                    payment.to_json_data()
                    for payment in payments
                ],
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        order_id = data.get("order_id")
        method = data.get("method")

        if not order_id or not method:
            return Response(
                {
                    "message": (
                        "order_id and method are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method not in Payment.METHOD_CHOICES:
            return Response(
                {
                    "message": "Invalid payment method",
                    "allowed_methods": list(
                        Payment.METHOD_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_order_by_id(order_id)

        if not order:
            return Response(
                {"message": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            user.role not in ["admin", "staff"]
            and order.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status == "cancelled":
            return Response(
                {
                    "message": (
                        "Cannot create payment "
                        "for cancelled order"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.payment_status == "paid":
            return Response(
                {
                    "message": "Order is already paid"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_payment = Payment.objects(
            order=order
        ).first()

        if existing_payment:
            return Response(
                {
                    "message": (
                        "Payment already exists "
                        "for this order"
                    ),
                    "data": (
                        existing_payment.to_json_data()
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment(
            order=order,
            user=order.user,
            amount=order.total_amount,
            method=method,
            status="pending",
        )
        payment.save()

        return Response(
            {
                "message": "Create payment successfully",
                "data": payment.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    @login_required
    def get(self, request, payment_id):
        payment = get_payment_by_id(payment_id)

        if not payment:
            return Response(
                {"message": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and payment.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": (
                    "Get payment detail successfully"
                ),
                "data": payment.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class PaymentConfirmView(APIView):
    @login_required
    def put(self, request, payment_id):
        user = request.current_user

        if user.role not in ["admin", "staff"]:
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payment = get_payment_by_id(payment_id)

        if not payment:
            return Response(
                {"message": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status == "paid":
            return Response(
                {
                    "message": (
                        "Payment is already confirmed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status in ["failed", "refunded"]:
            return Response(
                {
                    "message": (
                        "This payment cannot be confirmed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_code = request.data.get(
            "transaction_code"
        )

        if not transaction_code:
            transaction_code = (
                generate_transaction_code(
                    payment.method
                )
            )

        payment.status = "paid"
        payment.transaction_code = transaction_code
        payment.paid_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()
        payment.save()

        order = payment.order
        order.payment_status = "paid"
        order.updated_at = datetime.utcnow()
        order.save()

        return Response(
            {
                "message": (
                    "Confirm payment successfully"
                ),
                "data": payment.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class PaymentFailView(APIView):
    @login_required
    def put(self, request, payment_id):
        user = request.current_user

        if user.role not in ["admin", "staff"]:
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payment = get_payment_by_id(payment_id)

        if not payment:
            return Response(
                {"message": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status == "paid":
            return Response(
                {
                    "message": (
                        "Paid payment cannot be marked failed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == "failed":
            return Response(
                {
                    "message": (
                        "Payment is already failed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = "failed"
        payment.failure_reason = request.data.get(
            "failure_reason",
            "Payment failed",
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        return Response(
            {
                "message": "Mark payment failed successfully",
                "data": payment.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
