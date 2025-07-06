from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.utils.text import slugify
from shop.models import Category, Product, ProductImage, Order
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
# Create your views here.
def index(request):
    return render(request, 'Home/index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.type == 'ADMIN':
                login(request, user)
                messages.success(request, 'Login successfully!')
                return redirect('index')
            else:
                messages.error(request, 'Invalid user role')
                return redirect('login')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'authentication/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

################################################################
@login_required
def categories(request):
    categories = Category.objects.prefetch_related('products').all()
    return render(request, 'Home/categories.html', {'categories': categories})

def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('category_name')
        image = request.FILES.get('category_image')

        image_path = ''
        if image:
            # Save image manually to media folder
            from django.core.files.storage import FileSystemStorage
            fs = FileSystemStorage(location='media/category_images/')
            filename = fs.save(image.name, image)
            image_path = 'category_images/' + filename

        # Save to database
        Category.objects.create(
            name=name,
            imageUrl=image_path
        )

        return redirect('categories')  # or render a page with categories

def update_category(request):
    if request.method == 'POST':
        new_name = request.POST.get('category_name')
        new_image = request.FILES.get('category_image')

        # Get category or return 404
        category = get_object_or_404(Category, name=new_name)

        # Update the name and slug
        if new_name:
            category.name = new_name
            category.slug = slugify(new_name)

        # If image is provided, update it
        if new_image:
            # Save image manually to media folder
            from django.core.files.storage import FileSystemStorage
            fs = FileSystemStorage(location='media/category_images/')
            filename = fs.save(new_image.name, new_image)
            image_path = 'category_images/' + filename
            category.imageUrl = image_path

        category.save()

        messages.success(request, f'Category "{category.name}" updated successfully!')
        return redirect('categories')  # Replace with your actual category list URL name

    else:
        messages.error(request, 'Invalid request method.')
        return redirect('categories')

def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    messages.success(request, f'Category "{category.name}" deleted successfully!')
    return redirect('categories')

@login_required
def products(request):
    categories = Category.objects.all()
    products = Product.objects.prefetch_related('images', 'category').all()
    return render(request, 'Home/products.html', {'categories': categories, 'products': products})

def add_product(request):
    if request.method == 'POST':
        title = request.POST.get('product_title')
        category_id = request.POST.get('category')
        price = request.POST.get('product_price')
        max_quantity = request.POST.get('product_max_quantity')
        hero_image_file = request.FILES.get('product_hero_image')
        product_images = request.FILES.getlist('product_images[]')

        # Handle slug and category
        slug = slugify(title)
        category = Category.objects.filter(id=category_id).first()

        # Save hero image if available
        hero_image_path = ''
        if hero_image_file:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'products'))
            filename = fs.save(hero_image_file.name, hero_image_file)
            hero_image_path = f'products/{filename}'

        # Save Product
        product = Product.objects.create(
            category=category,
            title=title,
            slug=slug,
            price=int(price) if price else None,
            heroImage=hero_image_path,
            maxQuantity=int(max_quantity) if max_quantity else None,
        )

        # Save additional product images
        for image in product_images:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'products'))
            filename = fs.save(image.name, image)
            image_path = f'products/{filename}'

            ProductImage.objects.create(
                product=product,
                image_url=image_path,
            )

        messages.success(request, "Product added successfully!")
        return redirect('products')  # Change this to your actual product list view

    categories = Category.objects.all()
    return render(request, 'Home/products.html', {'categories': categories})

# not tested yet
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.title = request.POST.get('title')
        product.slug = slugify(product.title)
        product.price = request.POST.get('price')
        product.maxQuantity = request.POST.get('max_quantity')
        product.category_id = request.POST.get('category')

        # Handle hero image update
        hero_image = request.FILES.get('hero_image')
        if hero_image:
            image_path = f'products/hero/{hero_image.name}'
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            with open(full_path, 'wb+') as destination:
                for chunk in hero_image.chunks():
                    destination.write(chunk)
            product.heroImage = image_path

        product.save()

        # Handle additional product images
        product_images = request.FILES.getlist('product_images[]')
        for image in product_images:
            image_path = f'products/gallery/{image.name}'
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            with open(full_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            ProductImage.objects.create(product=product, image_url=image_path)

        return redirect('product_list')  # Redirect to your product list view

    categories = Category.objects.all()
    return render(request, 'edit_product.html', {'product': product, 'categories': categories})

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, f'product "{product.title}" deleted successfully!')
    return redirect('products')

@login_required
def orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    return render(request, 'Home/orders.html', {'orders': orders})

@csrf_exempt  # Only use in development or if you're not sending CSRF token
@require_POST
def update_order_status(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')

        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_orders_{order.user.id}",
            {
                'type': 'order_update',
                'content': {
                    'order_id': order.id,
                    'status': order.status,
                }
            }
        )

        return JsonResponse({'success': True, 'message': 'Status updated successfully'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)