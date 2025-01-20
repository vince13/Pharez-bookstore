from django.contrib import admin
from .models import UserPreference, BookRecommendation

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user',)
    raw_id_fields = ('user',)
    filter_horizontal = ('favorite_genres',)

@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'score', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'book__title')
    raw_id_fields = ('user', 'book') 