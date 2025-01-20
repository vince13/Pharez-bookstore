from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import UserPreference, BookRecommendation
from .serializers import UserPreferenceSerializer, BookRecommendationSerializer
from books.models import Book
from orders.models import Order
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_user_preferences(self, user):
        """Get or create user preferences"""
        pref, _ = UserPreference.objects.get_or_create(user=user)
        return pref

    def get_user_history(self, user):
        """Get user's purchase and review history"""
        purchased_books = Book.objects.filter(
            orderitem__order__user=user
        ).distinct()
        
        reviewed_books = Book.objects.filter(
            review__user=user
        ).distinct()
        
        return purchased_books | reviewed_books

    def generate_recommendations(self, user):
        """Generate book recommendations based on user preferences and history"""
        preferences = self.get_user_preferences(user)
        user_history = self.get_user_history(user)
        
        # Get books with similar genres
        genre_recommendations = Book.objects.filter(
            genres__in=preferences.favorite_genres.all()
        ).exclude(
            id__in=user_history.values_list('id', flat=True)
        ).annotate(
            matching_genres=Count('genres')
        ).order_by('-matching_genres')[:10]

        # Content-based filtering using book descriptions
        if user_history.exists():
            # Prepare text data for TF-IDF
            all_books = Book.objects.exclude(id__in=user_history.values_list('id', flat=True))
            descriptions = [book.description for book in all_books]
            history_descriptions = [book.description for book in user_history]
            
            # Create TF-IDF matrix
            tfidf = TfidfVectorizer(stop_words='english')
            tfidf_matrix = tfidf.fit_transform(descriptions + history_descriptions)
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(
                tfidf_matrix[:-len(history_descriptions)],
                tfidf_matrix[-len(history_descriptions):]
            )
            
            # Get average similarity score for each book
            avg_scores = np.mean(similarity_scores, axis=1)
            similar_indices = np.argsort(avg_scores)[-10:][::-1]
            
            # Get content-based recommendations
            content_recommendations = [all_books[i] for i in similar_indices]
        else:
            content_recommendations = []

        # Combine and save recommendations
        recommendations = list(genre_recommendations) + content_recommendations
        
        # Clear old recommendations
        BookRecommendation.objects.filter(user=user).delete()
        
        # Save new recommendations
        for i, book in enumerate(recommendations):
            BookRecommendation.objects.create(
                user=user,
                book=book,
                score=1.0 - (i / len(recommendations))
            )

    @action(detail=False, methods=['get'])
    def get_recommendations(self, request):
        """Get recommendations for the current user"""
        self.generate_recommendations(request.user)
        recommendations = BookRecommendation.objects.filter(user=request.user)
        serializer = BookRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        """Get or update user preferences"""
        preferences = self.get_user_preferences(request.user)
        
        if request.method == 'PUT':
            serializer = UserPreferenceSerializer(preferences, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserPreferenceSerializer(preferences)
        return Response(serializer.data) 