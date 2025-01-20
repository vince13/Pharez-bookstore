from rest_framework import serializers
from .models import Book, Genre, Review

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'book', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

class BookSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        write_only=True,
        queryset=Genre.objects.all(),
        source='genres'
    )
    average_rating = serializers.FloatField(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True, source='review_set')

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'price', 
            'stock', 'cover_image', 'seller', 'genres', 'genre_ids',
            'average_rating', 'reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['seller'] 