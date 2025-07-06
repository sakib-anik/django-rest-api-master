from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from shop.serializers import RegisterUserSerializer, CategorySerializer, ProductSerializer, OrderSerializer
from shop.models import CustomUser, Category, Product, ProductImage, Order, OrderItem
from django.contrib.auth import login, authenticate, logout
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

@api_view(['POST'])
def loginUserApi(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if not CustomUser.objects.filter(email=email).exists():
        return Response({'detail': 'User does not exist with this email.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=email, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        user_serializer = RegisterUserSerializer(user)

        return Response({
            'message': 'Signed in successfully',
            'refresh': str(refresh),
            'token': str(refresh.access_token),
            'user': user_serializer.data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({'detail': 'Email or Password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def registerUserApi(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if CustomUser.objects.filter(email=email).exists():
        return Response({'detail': 'User already exists with this email.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        username=email  # Using email as username
    )

    refresh = RefreshToken.for_user(user)
    user_serializer = RegisterUserSerializer(user)

    return Response({
        'message': 'Signed up successfully',
        'refresh': str(refresh),
        'token': str(refresh.access_token),
        'user': user_serializer.data
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logoutUserApi(request):
    # No actual token invalidation here, just a client-side logout signal
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getLoggedInUserProfileApi(request):
    user = request.user  # Automatically resolved from JWT
    return Response({
        'id': user.id,
        'email': user.email,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProductsAndCategoriesApi(request):
    categories = Category.objects.prefetch_related('products').all()
    serialized_categories = CategorySerializer(categories, many=True)
    products = Product.objects.select_related('category').all()
    serialized_products = ProductSerializer(products, many=True)
    return Response({
        'categories': serialized_categories.data,
        'products': serialized_products.data,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCategoryAndProductsApi(request, slug):
    category = get_object_or_404(Category.objects.prefetch_related('products'), slug=slug)
    serialized_category = CategorySerializer(category)
    return Response(serialized_category.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProductDetailsApi(request, slug):
    product = get_object_or_404(Product.objects.select_related('category').prefetch_related('images'), slug=slug)
    serialized_product = ProductSerializer(product)
    return Response(serialized_product.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order_api(request):
    
    serializer = OrderSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        with transaction.atomic():
            order_data = serializer.validated_data
            items_data = order_data.pop('items')

            # Create Order
            order = Order.objects.create(user=request.user, **order_data)

            # Create OrderItems
            for item in items_data:
                product = item['product']
                quantity = item['quantity']

                if product.maxQuantity is None or product.maxQuantity < quantity:
                    transaction.set_rollback(True)
                    return Response(
                        {"detail": f"Insufficient quantity for {product.title}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Decrease quantity
                product.maxQuantity -= quantity
                product.save()

                OrderItem.objects.create(order=order, product=product, quantity=quantity)

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_details_api(request, id, slug):
    order = get_object_or_404(Order, user_id=id, slug=slug)
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)


    