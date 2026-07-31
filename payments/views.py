import uuid
from datetime import datetime

from bson import ObjectId
from mongoengine.queryset.visitor import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from orders.documents import Order
from payments.documents import Payment
from users.documents import User

from notifications.services import create_notification


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
        search = request.query_params.get(
            "search",
            "",
        ).strip()
        payment_status = request.query_params.get("status")
        method = request.query_params.get("method")

        if user.role in ["admin", "staff"]:
            payments = Payment.objects()
        else:
            payments = Payment.objects(user=user)

        if search:
            matching_user_ids = [
                item.id
                for item in User.objects(
                    Q(full_name__icontains=search)
                    | Q(email__icontains=search)
                ).only("id")
            ]

            matching_order_ids = [
                item.id
                for item in Order.objects(
                    code__icontains=search
                ).only("id")
            ]

            search_query = (
                Q(transaction_code__icontains=search)
                | Q(failure_reason__icontains=search)
                | Q(refund_reason__icontains=search)
            )

            if matching_user_ids:
                search_query = (
                    search_query
                    | Q(user__in=matching_user_ids)
                )

            if matching_order_ids:
                search_query = (
                    search_query
                    | Q(order__in=matching_order_ids)
                )

            payments = payments.filter(search_query)

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

        create_notification(
            recipient=payment.user,
            notification_type="payment",
            title="Đã tạo yêu cầu thanh toán",
            message=(
                "Yêu cầu thanh toán của bạn đã được tạo "
                "và đang chờ xác nhận."
            ),
            related_id=str(payment.id),
            related_type="payment",
            data={
                "payment_id": str(payment.id),
                "status": payment.status,
                "amount": payment.amount,
            },
        )

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

        if payment.status != "pending":
            return Response(
                {
                    "message": (
                        "Only pending payment can be confirmed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.order.status == "cancelled":
            return Response(
                {
                    "message": (
                        "Cannot confirm payment for cancelled order"
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

        create_notification(
            recipient=payment.user,
            notification_type="payment",
            title="Thanh toán thành công",
            message=(
                "Giao dịch thanh toán của bạn "
                "đã hoàn tất thành công."
            ),
            related_id=str(payment.id),
            related_type="payment",
            data={
                "payment_id": str(payment.id),
                "status": payment.status,
                "amount": payment.amount,
            },
        )

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

        if payment.status != "pending":
            return Response(
                {
                    "message": (
                        "Only pending payment can be marked failed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        failure_reason = str(
            request.data.get(
                "failure_reason",
                "Payment failed",
            )
        ).strip()

        if not failure_reason:
            failure_reason = "Payment failed"

        if len(failure_reason) > 1000:
            return Response(
                {
                    "message": (
                        "failure_reason cannot exceed 1000 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = "failed"
        payment.failure_reason = failure_reason
        payment.updated_at = datetime.utcnow()
        payment.save()

        create_notification(
            recipient=payment.user,
            notification_type="payment",
            title="Thanh toán thất bại",
            message=(
                "Giao dịch thanh toán không thành công. "
                f"Lý do: {failure_reason}"
            ),
            related_id=str(payment.id),
            related_type="payment",
            data={
                "payment_id": str(payment.id),
                "status": payment.status,
                "failure_reason": failure_reason,
            },
        )

        return Response(
            {
                "message": "Mark payment failed successfully",
                "data": payment.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class PaymentRefundView(APIView):
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

        if payment.status != "paid":
            return Response(
                {
                    "message": (
                        "Only paid payment can be refunded"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        refund_reason = str(
            request.data.get(
                "refund_reason",
                "Refund approved",
            )
        ).strip()

        if not refund_reason:
            refund_reason = "Refund approved"

        if len(refund_reason) > 1000:
            return Response(
                {
                    "message": (
                        "refund_reason cannot exceed 1000 characters"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = datetime.utcnow()

        payment.status = "refunded"
        payment.refund_reason = refund_reason
        payment.refunded_at = now
        payment.updated_at = now
        payment.save()

        order = payment.order
        order.payment_status = "refunded"
        order.updated_at = now
        order.save()

        create_notification(
            recipient=payment.user,
            notification_type="payment",
            title="Thanh toán đã được hoàn tiền",
            message=(
                "Giao dịch của bạn đã được hoàn tiền. "
                f"Lý do: {refund_reason}"
            ),
            related_id=str(payment.id),
            related_type="payment",
            data={
                "payment_id": str(payment.id),
                "status": payment.status,
                "refund_reason": refund_reason,
                "amount": payment.amount,
            },
        )

        return Response(
            {
                "message": "Refund payment successfully",
                "data": payment.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
