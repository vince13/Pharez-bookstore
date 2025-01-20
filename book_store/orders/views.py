from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from books.models import Book

class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_or_create_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_or_create_cart()
        serializer = CartItemSerializer(data=request.data)
        
        if serializer.is_valid():
            book = serializer.validated_data['book']
            quantity = serializer.validated_data['quantity']
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                book=book,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response(CartItemSerializer(cart_item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart = self.get_or_create_cart()
        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create order from cart
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price()
        )

        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                quantity=cart_item.quantity,
                price=cart_item.book.price
            )

        # Clear the cart
        cart.items.all().delete()

        return Response(
            OrderSerializer(order).data, 
            status=status.HTTP_201_CREATED
        )

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user) 

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'cart_items': cart.items.all()
    }
    return render(request, 'orders/cart.html', context)

@login_required
def add_to_cart(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            book=book,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'{book.title} added to cart.')
    
    return redirect('home')

@login_required
def remove_from_cart(request, book_id):
    cart = Cart.objects.get(user=request.user)
    book = get_object_or_404(Book, id=book_id)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, book=book)
        cart_item.delete()
        messages.success(request, f'{book.title} removed from cart.')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart.')
    
    return redirect('orders:cart') 

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:cart')
            
        # Create order from cart
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price()
        )

        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                quantity=cart_item.quantity,
                price=cart_item.book.price
            )

        # Clear the cart
        cart.items.all().delete()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('orders:order_confirmation', order_id=order.id)
        
    return render(request, 'orders/checkout.html', {'cart': cart}) 