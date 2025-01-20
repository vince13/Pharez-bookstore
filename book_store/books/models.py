from django.db import models
from accounts.models import User
from django.utils.text import slugify
from django.urls import reverse
import uuid

class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Book(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    cover_image = models.ImageField(upload_to='book_covers/')
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    genres = models.ManyToManyField(Genre)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Statistics fields
    view_count = models.PositiveIntegerField(default=0)
    sale_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['seller', 'status']),
        ]
    
    def generate_unique_slug(self):
        """Generate a unique slug for the book."""
        base_slug = slugify(self.title)
        if not Book.objects.filter(slug=base_slug).exists():
            return base_slug
        
        # If the base slug exists, append a UUID4 to make it unique
        return f"{base_slug}-{str(uuid.uuid4())[:8]}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('books:book_detail', kwargs={'slug': self.slug})
    
    @property
    def average_rating(self):
        ratings = self.review_set.all()
        if ratings:
            return sum(review.rating for review in ratings) / len(ratings)
        return 0
    
    @property
    def total_reviews(self):
        return self.review_set.count()
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_sale_count(self):
        self.sale_count += 1
        self.save(update_fields=['sale_count'])
    
    def toggle_favorite(self, user):
        favorite, created = Favorite.objects.get_or_create(book=self, user=user)
        if not created:
            favorite.delete()
            self.favorite_count -= 1
        else:
            self.favorite_count += 1
        self.save(update_fields=['favorite_count'])
        return created

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('book', 'user')
        ordering = ['-created_at']

class Favorite(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('book', 'user') 