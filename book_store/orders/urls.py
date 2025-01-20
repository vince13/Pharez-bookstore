from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/cart', views.CartViewSet, basename='api_cart')
router.register(r'api/orders', views.OrderViewSet, basename='api_order')

app_name = 'orders'

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
] 