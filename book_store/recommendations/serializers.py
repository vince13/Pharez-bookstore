from rest_framework import serializers
from .models import UserPreference, BookRecommendation
from books.models import Genre
from books.serializers import BookSerializer, GenreSerializer

class UserPreferenceSerializer(serializers.ModelSerializer):
    favorite_genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Genre.objects.all(),
        source='favorite_genres'
    )

    class Meta:
        model = UserPreference
        fields = ['id', 'favorite_genres', 'genre_ids']

class BookRecommendationSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = BookRecommendation
        fields = ['id', 'book', 'score', 'created_at'] 