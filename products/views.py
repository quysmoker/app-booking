from datetime import datetime

from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import role_required
from products.documents import Product


def get_product_by_id(product_id):
    try:
        return Product.objects(id=ObjectId(product_id)).first()
    except Exception:
        return None


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_boolean(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.lower().strip()

        if value == "true":
            return True

        if value == "false":
            return False

    return None


class ProductListCreateView(APIView):
    def get(self, request):
        products = Product.objects(is_active=True)

        category = request.query_params.get("category")
        brand = request.query_params.get("brand")
        keyword = request.query_params.get("keyword")

        if category:
            products = products.filter(category=category)

        if brand:
            products = products.filter(brand__iexact=brand)

        if keyword:
            products = products.filter(name__icontains=keyword)

        return Response(
            {
                "message": "Get products successfully",
                "data": [
                    product.to_json_data()
                    for product in products
                ],
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def post(self, request):
        data = request.data

        name = data.get("name")
        category = data.get("category")
        price = parse_float(data.get("price"))
        stock = parse_int(data.get("stock", 0))

        if not name or not category:
            return Response(
                {
                    "message": (
                        "name and category are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category not in Product.CATEGORY_CHOICES:
            return Response(
                {
                    "message": "Invalid product category",
                    "allowed_categories": list(
                        Product.CATEGORY_CHOICES
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if price is None or price < 0:
            return Response(
                {
                    "message": (
                        "price must be a valid non-negative number"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if stock is None or stock < 0:
            return Response(
                {
                    "message": (
                        "stock must be a valid non-negative integer"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        images = data.get("images", [])

        if not isinstance(images, list):
            return Response(
                {"message": "images must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = Product(
            name=name.strip(),
            description=data.get("description", ""),
            category=category,
            brand=data.get("brand", ""),
            price=price,
            stock=stock,
            image=data.get("image", ""),
            images=images,
            is_active=True,
        )
        product.save()

        return Response(
            {
                "message": "Create product successfully",
                "data": product.to_json_data(),
            },
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(APIView):
    def get(self, request, product_id):
        product = get_product_by_id(product_id)

        if not product or not product.is_active:
            return Response(
                {"message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": "Get product detail successfully",
                "data": product.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def put(self, request, product_id):
        product = get_product_by_id(product_id)

        if not product:
            return Response(
                {"message": "Product not found"},
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

            product.name = name

        if data.get("description") is not None:
            product.description = data.get("description")

        if data.get("category") is not None:
            category = data.get("category")

            if category not in Product.CATEGORY_CHOICES:
                return Response(
                    {
                        "message": "Invalid product category",
                        "allowed_categories": list(
                            Product.CATEGORY_CHOICES
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.category = category

        if data.get("brand") is not None:
            product.brand = data.get("brand")

        if data.get("price") is not None:
            price = parse_float(data.get("price"))

            if price is None or price < 0:
                return Response(
                    {
                        "message": (
                            "price must be a valid "
                            "non-negative number"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.price = price

        if data.get("stock") is not None:
            stock = parse_int(data.get("stock"))

            if stock is None or stock < 0:
                return Response(
                    {
                        "message": (
                            "stock must be a valid "
                            "non-negative integer"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.stock = stock

        if data.get("image") is not None:
            product.image = data.get("image")

        if data.get("images") is not None:
            images = data.get("images")

            if not isinstance(images, list):
                return Response(
                    {"message": "images must be a list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.images = images

        if data.get("is_active") is not None:
            is_active = parse_boolean(data.get("is_active"))

            if is_active is None:
                return Response(
                    {
                        "message": (
                            "is_active must be true or false"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.is_active = is_active

        product.updated_at = datetime.utcnow()
        product.save()

        return Response(
            {
                "message": "Update product successfully",
                "data": product.to_json_data(),
            },
            status=status.HTTP_200_OK,
        )

    @role_required(["admin", "staff"])
    def delete(self, request, product_id):
        product = get_product_by_id(product_id)

        if not product:
            return Response(
                {"message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        product.is_active = False
        product.updated_at = datetime.utcnow()
        product.save()

        return Response(
            {"message": "Delete product successfully"},
            status=status.HTTP_200_OK,
        )
