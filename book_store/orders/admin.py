from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem
from django.utils import timezone
from datetime import timedelta

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ('book',)
    extra = 0

class RecentOrderFilter(admin.SimpleListFilter):
    title = 'order period'
    parameter_name = 'order_period'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(created_at__date=timezone.now().date())
        if self.value() == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=week_ago)
        if self.value() == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=month_ago)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', RecentOrderFilter)
    search_fields = ('user__username', 'id')
    raw_id_fields = ('user',)
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['mark_as_shipped', 'mark_as_delivered']

    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status='PAID').update(status='SHIPPED')
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status='SHIPPED').update(status='DELIVERED')
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"

class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ('book',)
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    inlines = [CartItemInline] 