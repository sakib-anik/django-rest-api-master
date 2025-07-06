from rest_framework import serializers
from shop.models import CustomUser, Category, Product, ProductImage, OrderItem, Order

class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'password', 'expo_notification_token']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image_url']

class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['imageUrl', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = SimpleCategorySerializer(read_only=True)  # ✅ no recursion

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'heroImage', 'images', 'price', 'maxQuantity', 'category']

class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'imageUrl', 'slug', 'created_at', 'products']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'created_at']
        read_only_fields = ['id', 'created_at', 'product']

class UserIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = UserIdSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'slug', 'description', 'status', 'totalPrice', 'created_at', 'user', 'items']
        read_only_fields = ['id', 'slug', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item in items_data:
            OrderItem.objects.create(order=order, **item)
        return order