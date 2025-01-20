from django.contrib import admin
from .models import Book, Genre, Review
from django.db.models import Avg

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class StockFilter(admin.SimpleListFilter):
    title = 'stock status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('out', 'Out of Stock'),
            ('low', 'Low Stock (< 10)'),
            ('available', 'In Stock'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'out':
            return queryset.filter(stock=0)
        if self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lt=10)
        if self.value() == 'available':
            return queryset.filter(stock__gte=10)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock', 'seller', 'get_average_rating', 'created_at')
    list_filter = ('genres', 'created_at', StockFilter)
    search_fields = ('title', 'author', 'description')
    raw_id_fields = ('seller',)
    date_hierarchy = 'created_at'

    def get_average_rating(self, obj):
        return obj.review_set.aggregate(Avg('rating'))['rating__avg'] or 0
    get_average_rating.short_description = 'Avg Rating'

    actions = ['mark_out_of_stock']

    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f'{updated} books marked as out of stock.')
    mark_out_of_stock.short_description = "Mark selected books as out of stock"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    raw_id_fields = ('book', 'user') 