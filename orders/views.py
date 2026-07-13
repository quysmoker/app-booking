import uuid
from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from carts.documents import Cart
from orders.documents import Order, OrderItem
from products.documents import Product


def get_order_by_id(order_id):
    try:
        return Order.objects(
            id=ObjectId(order_id)
        ).first()
    except Exception:
        return None


def generate_order_code():
    while True:
        code = f"ORD-{uuid.uuid4().hex[:10].upper()}"

        if not Order.objects(code=code).first():
            return code


def restore_order_stock(order):
    for item in order.items:
        try:
            product = Product.objects(
                id=ObjectId(item.product_id)
            ).first()

            if product:
                product.stock += item.quantity
                product.updated_at = datetime.utcnow()
                product.save()

        except Exception:
            continue


class OrderListCreateView(APIView):
    @login_required
    def get(self, request):
        user = request.current_user
        order_status = request.query_params.get("status")

        if user.role in ["admin", "staff"]:
            orders = Order.objects()
        else:
            orders = Order.objects(user=user)

        if order_status:
            if order_status not in Order.STATUS_CHOICES:
                return Response(
                    {
                        "message": "Invalid order status",
                        "allowed_statuses": list(
                            Order.STATUS_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            orders = orders.filter(status=order_status)

        return Response(
            {
                "message": "Get orders successfully",
                "data": [
                    order.to_json_data()
                    for order in orders
                ],
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        recipient_name = data.get("recipient_name")
        recipient_phone = data.get("recipient_phone")
        shipping_address = data.get("shipping_address")
        payment_method = data.get(
            "payment_method",
            "cod",
        )

        if (
            not recipient_name
            or not recipient_phone
            or not shipping_address
        ):
            return Response(
                {
                    "message": (
                        "recipient_name, recipient_phone "
                        "and shipping_address are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_method not in Order.PAYMENT_METHOD_CHOICES:
            return Response(
                {
                    "message": "Invalid payment method",
                    "allowed_payment_methods": list(
                        Order.PAYMENT_METHOD_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = Cart.objects(user=user).first()

        if not cart or not cart.items:
            return Response(
                {"message": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_items = []
        subtotal = 0
        products_to_update = []

        # Kiểm tra toàn bộ sản phẩm trước khi trừ kho
        for cart_item in cart.items:
            try:
                product = Product.objects(
                    id=cart_item.product.id,
                    is_active=True,
                ).first()
            except Exception:
                product = None

            if not product:
                return Response(
                    {
                        "message": (
                            "A product in the cart "
                            "does not exist or is inactive"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if cart_item.quantity > product.stock:
                return Response(
                    {
                        "message": (
                            f"Product '{product.name}' "
                            "does not have enough stock"
                        ),
                        "product_id": str(product.id),
                        "available_stock": product.stock,
                        "requested_quantity": (
                            cart_item.quantity
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item_subtotal = (
                product.price * cart_item.quantity
            )

            order_items.append(
                OrderItem(
                    product_id=str(product.id),
                    product_name=product.name,
                    product_image=product.image or "",
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    subtotal=item_subtotal,
                )
            )

            products_to_update.append(
                {
                    "product": product,
                    "quantity": cart_item.quantity,
                }
            )

            subtotal += item_subtotal

        try:
            shipping_fee = float(
                data.get("shipping_fee", 0)
            )
        except (TypeError, ValueError):
            return Response(
                {
                    "message": (
                        "shipping_fee must be a valid number"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if shipping_fee < 0:
            return Response(
                {
                    "message": (
                        "shipping_fee cannot be negative"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        discount_amount = 0
        total_amount = max(
            subtotal + shipping_fee - discount_amount,
            0,
        )

        updated_products = []

        # Trừ kho theo điều kiện stock vẫn còn đủ
        for item in products_to_update:
            product = item["product"]
            quantity = item["quantity"]

            current_product = Product.objects(
                id=product.id,
                stock__gte=quantity,
                is_active=True,
            ).first()

            if not current_product:
                for updated_item in updated_products:
                    restored_product = Product.objects(
                        id=updated_item["product"].id
                    ).first()

                    if restored_product:
                        restored_product.stock += updated_item["quantity"]
                        restored_product.updated_at = datetime.utcnow()
                        restored_product.save()

                return Response(
                    {
                        "message": (
                            f"Product '{product.name}' "
                            "does not have enough stock"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_product.stock -= quantity
            current_product.updated_at = datetime.utcnow()
            current_product.save()

            updated_products.append(
                {
                    "product": current_product,
                    "quantity": quantity,
                }
            )

        try:
            order = Order(
                code=generate_order_code(),
                user=user,
                items=order_items,
                recipient_name=recipient_name.strip(),
                recipient_phone=recipient_phone.strip(),
                shipping_address=shipping_address.strip(),
                note=data.get("note", ""),
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                discount_amount=discount_amount,
                total_amount=total_amount,
                status="pending",
                payment_method=payment_method,
                payment_status="unpaid",
            )
            order.save()

        except Exception:
            # Nếu lưu order lỗi thì hoàn lại stock
            for updated_item in updated_products:
                Product.objects(
                    id=updated_item["product"].id
                ).update_one(
                    inc__stock=updated_item["quantity"]
                )

            return Response(
                {"message": "Create order failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Xóa giỏ hàng sau khi tạo đơn thành công
        cart.items = []
        cart.updated_at = datetime.utcnow()
        cart.save()

        return Response(
            {
                "message": "Create order successfully",
                "data": order.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    @login_required
    def get(self, request, order_id):
        order = get_order_by_id(order_id)

        if not order:
            return Response(
                {"message": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and order.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": (
                    "Get order detail successfully"
                ),
                "data": order.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class OrderStatusUpdateView(APIView):
    @login_required
    def put(self, request, order_id):
        user = request.current_user

        if user.role not in ["admin", "staff"]:
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = get_order_by_id(order_id)

        if not order:
            return Response(
                {"message": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")

        transitions = {
            "pending": ["confirmed"],
            "confirmed": ["shipping"],
            "shipping": ["completed"],
            "completed": [],
            "cancelled": [],
        }

        allowed_statuses = transitions.get(
            order.status,
            [],
        )

        if new_status not in allowed_statuses:
            return Response(
                {
                    "message": "Invalid status transition",
                    "current_status": order.status,
                    "allowed_statuses": allowed_statuses,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.updated_at = datetime.utcnow()
        order.save()

        return Response(
            {
                "message": (
                    "Update order status successfully"
                ),
                "data": order.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class OrderCancelView(APIView):
    @login_required
    def delete(self, request, order_id):
        order = get_order_by_id(order_id)

        if not order:
            return Response(
                {"message": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.current_user

        if (
            user.role not in ["admin", "staff"]
            and order.user.id != user.id
        ):
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status not in ["pending", "confirmed"]:
            return Response(
                {
                    "message": (
                        "Only pending or confirmed "
                        "orders can be cancelled"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        restore_order_stock(order)

        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()

        if order.payment_status == "paid":
            order.payment_status = "refunded"

        order.save()

        return Response(
            {
                "message": "Cancel order successfully",
                "data": order.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
