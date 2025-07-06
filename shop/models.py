from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
import uuid
from django.utils.text import slugify
# Create your models here.
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('USER', 'USER'),
        ('ADMIN', 'ADMIN'),
    ]
    type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='USER'
    )
    avatar_url = models.TextField(default='https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
    )
    expo_notification_token = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.username

def generate_token():
    return get_random_string(32)


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(max_length=100)
    token = models.CharField(max_length=32, default=generate_token, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    TOKEN_VALIDITY_PERIOD = timezone.timedelta(hours=1)

    def is_valid(self):
        return timezone.now() < self.created_at + self.TOKEN_VALIDITY_PERIOD

    def send_reset_email(self):
        reset_link = f"http://localhost:8000/reset_password/{self.token}/"
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )
        

############################################################################################################
class Category(models.Model):
    name = models.TextField(unique=True)
    imageUrl = models.TextField(blank=True, null=True)
    slug = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL, related_name='products')
    title = models.TextField(unique=True)
    slug = models.SlugField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    heroImage = models.TextField(blank=True, null=True)  # If storing image URL. Use ImageField if uploading.
    maxQuantity = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name='images')
    image_url = models.TextField(blank=True, null=True)  # Use ImageField if uploading files
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} Image"

class Order(models.Model):
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL, related_name='orders')
    slug = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    totalPrice = models.FloatField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            self.slug = slugify(f"order-{self.user.id}-{timestamp}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.SET_NULL, related_name='items')
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    quantity = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.title} in Order #{self.order.id}"


