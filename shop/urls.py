from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register-user/', views.registerUserApi),          
    path('login-user/', views.loginUserApi),          
    path('profile/', views.getLoggedInUserProfileApi),      
    path('logout-user/', views.logoutUserApi, name='logout-user'),
    path('get-products-and-categories/', views.getProductsAndCategoriesApi),
    path('get-product-details/<str:slug>/', views.getProductDetailsApi, name='get_product_details'),
    path('get-category-and-products/<str:slug>/', views.getCategoryAndProductsApi),
    path('orders/', views.get_user_orders, name='get_user_orders'),
    path('place-order/', views.place_order_api, name='place_order'),
    path('orders/<int:id>/<slug:slug>/', views.order_details_api, name='order-detail-by-slug'),
]