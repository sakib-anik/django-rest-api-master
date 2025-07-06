from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.index, name='index'),
    path('categories/', views.categories, name='categories'),
    path('products/', views.products, name='products'),
    path('orders/', views.orders, name='orders'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-product/', views.add_product, name='add_product'),
    path('update-category/', views.update_category, name='update_category'),
    path('delete-category/<int:id>', views.delete_category, name='delete_category'),
    path('delete-product/<int:id>', views.delete_product, name='delete_product'),
    path('update-product/<int:id>', views.update_product, name='update_product'),
    path('update-order-status/', views.update_order_status, name='update-order-status'),
]