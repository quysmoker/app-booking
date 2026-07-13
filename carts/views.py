from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import login_required
from carts.documents import Cart, CartItem
from products.documents import Product


def get_product_by_id(product_id):
    try:
        return Product.objects(
            id=ObjectId(product_id)
        ).first()
    except Exception:
        return None


def get_or_create_cart(user):
    cart = Cart.objects(user=user).first()

    if not cart:
        cart = Cart(
            user=user,
            items=[],
        )
        cart.save()

    return cart


def parse_quantity(value):
    try:
        quantity = int(value)

        if quantity < 1:
            return None

        return quantity
    except (TypeError, ValueError):
        return None


def find_cart_item(cart, product_id):
    for item in cart.items:
        if (
            item.product
            and str(item.product.id) == str(product_id)
        ):
            return item

    return None


def remove_invalid_items(cart):
    valid_items = []

    for item in cart.items:
        try:
            product = item.product

            if product:
                valid_items.append(item)
        except Exception:
            continue

    if len(valid_items) != len(cart.items):
        cart.items = valid_items
        cart.updated_at = datetime.utcnow()
        cart.save()


class CartDetailView(APIView):
    @login_required
    def get(self, request):
        cart = get_or_create_cart(
            request.current_user
        )

        remove_invalid_items(cart)

        return Response(
            {
                "message": "Get cart successfully",
                "data": cart.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class CartAddItemView(APIView):
    @login_required
    def post(self, request):
        user = request.current_user
        data = request.data

        product_id = data.get("product_id")
        quantity = parse_quantity(
            data.get("quantity", 1)
        )

        if not product_id:
            return Response(
                {
                    "message": "product_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity is None:
            return Response(
                {
                    "message": (
                        "quantity must be an integer "
                        "greater than 0"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_product_by_id(product_id)

        if not product or not product.is_active:
            return Response(
                {
                    "message": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if product.stock <= 0:
            return Response(
                {
                    "message": "Product is out of stock"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = get_or_create_cart(user)

        existing_item = find_cart_item(
            cart,
            product_id,
        )

        if existing_item:
            new_quantity = (
                existing_item.quantity + quantity
            )

            if new_quantity > product.stock:
                return Response(
                    {
                        "message": (
                            "Quantity exceeds available stock"
                        ),
                        "available_stock": product.stock,
                        "current_cart_quantity": (
                            existing_item.quantity
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_item.quantity = new_quantity
            existing_item.unit_price = product.price
            existing_item.updated_at = datetime.utcnow()

        else:
            if quantity > product.stock:
                return Response(
                    {
                        "message": (
                            "Quantity exceeds available stock"
                        ),
                        "available_stock": product.stock,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item = CartItem(
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )

            cart.items.append(cart_item)

        cart.updated_at = datetime.utcnow()
        cart.save()

        return Response(
            {
                "message": (
                    "Add product to cart successfully"
                ),
                "data": cart.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class CartItemDetailView(APIView):
    @login_required
    def put(self, request, product_id):
        user = request.current_user
        data = request.data

        quantity = parse_quantity(
            data.get("quantity")
        )

        if quantity is None:
            return Response(
                {
                    "message": (
                        "quantity must be an integer "
                        "greater than 0"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_product_by_id(product_id)

        if not product or not product.is_active:
            return Response(
                {
                    "message": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if quantity > product.stock:
            return Response(
                {
                    "message": (
                        "Quantity exceeds available stock"
                    ),
                    "available_stock": product.stock,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = Cart.objects(user=user).first()

        if not cart:
            return Response(
                {
                    "message": "Cart not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item = find_cart_item(
            cart,
            product_id,
        )

        if not cart_item:
            return Response(
                {
                    "message": (
                        "Product is not in the cart"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item.quantity = quantity
        cart_item.unit_price = product.price
        cart_item.updated_at = datetime.utcnow()

        cart.updated_at = datetime.utcnow()
        cart.save()

        return Response(
            {
                "message": (
                    "Update cart item successfully"
                ),
                "data": cart.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @login_required
    def delete(self, request, product_id):
        user = request.current_user

        cart = Cart.objects(user=user).first()

        if not cart:
            return Response(
                {
                    "message": "Cart not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item = find_cart_item(
            cart,
            product_id,
        )

        if not cart_item:
            return Response(
                {
                    "message": (
                        "Product is not in the cart"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart.items.remove(cart_item)
        cart.updated_at = datetime.utcnow()
        cart.save()

        return Response(
            {
                "message": (
                    "Remove product from cart successfully"
                ),
                "data": cart.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )


class CartClearView(APIView):
    @login_required
    def delete(self, request):
        user = request.current_user

        cart = Cart.objects(user=user).first()

        if not cart:
            return Response(
                {
                    "message": "Cart is already empty"
                },
                status=status.HTTP_200_OK,
            )

        cart.items = []
        cart.updated_at = datetime.utcnow()
        cart.save()

        return Response(
            {
                "message": "Clear cart successfully",
                "data": cart.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )
