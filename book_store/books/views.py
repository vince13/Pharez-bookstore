from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import csv
import io
from django.http import HttpResponse, JsonResponse

from .models import Book, Genre, Review
from .forms import ReviewForm, BookForm

def book_list(request):
    # Only get published books for the public list
    books = Book.objects.filter(status='published')
    genres = Genre.objects.all().order_by('name')
    
    # Get selected genres from request
    selected_genres = request.GET.getlist('genre')
    
    # Filter books if genres are selected
    if selected_genres:
        books = books.filter(genres__slug__in=selected_genres)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        books = books.filter(price__gte=min_price)
    if max_price:
        books = books.filter(price__lte=max_price)

    # Pagination
    paginator = Paginator(books, 9)  # 9 books per page
    page = request.GET.get('page')
    books = paginator.get_page(page)

    context = {
        'books': books,
        'genres': genres,
        'selected_genres': selected_genres,
    }
    return render(request, 'books/book_list.html', context)

def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    similar_books = Book.objects.filter(
        status='published',
        genres__in=book.genres.all()
    ).exclude(id=book.id).distinct()[:3]
    
    # Increment view count
    book.increment_view_count()
    
    context = {
        'book': book,
        'similar_books': similar_books,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def add_review(request, slug):
    book = get_object_or_404(Book, slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been added.')
        else:
            messages.error(request, 'There was an error with your review.')
    
    return redirect('books:book_detail', slug=slug)

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.seller = request.user
            book.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Book added successfully!')
            return redirect('books:book_detail', slug=book.slug)
    else:
        form = BookForm()
    
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Add Book',
        'button_text': 'Add Book'
    })

@login_required
def edit_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    
    # Check if the user is the seller of the book
    if book.seller != request.user:
        messages.error(request, 'You do not have permission to edit this book.')
        return redirect('books:book_detail', slug=slug)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('books:book_detail', slug=book.slug)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Edit Book',
        'button_text': 'Update Book'
    })

@login_required
def delete_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    
    # Check if the user is the seller of the book
    if book.seller != request.user:
        messages.error(request, 'You do not have permission to delete this book.')
        return redirect('books:book_detail', slug=slug)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully!')
        return redirect('books:my_books')
    
    return render(request, 'books/book_confirm_delete.html', {'book': book})

@login_required
def my_books(request):
    # Get base queryset of user's books
    books = Book.objects.filter(seller=request.user)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status in ['published', 'draft', 'archived']:
        books = books.filter(status=status)
    
    # Order by status (published first, then drafts, then archived) and creation date
    books = books.order_by('-status', '-created_at')
    
    # Pagination
    paginator = Paginator(books, 9)  # 9 books per page
    page = request.GET.get('page')
    books = paginator.get_page(page)
    
    return render(request, 'books/my_books.html', {'books': books}) 

@login_required
def export_books(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="books_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Author', 'Description', 'Price', 'Stock', 'Genres', 'Status'])
    
    books = Book.objects.filter(seller=request.user)
    for book in books:
        writer.writerow([
            book.title,
            book.author,
            book.description,
            book.price,
            book.stock,
            ', '.join(g.name for g in book.genres.all()),
            book.status
        ])
    
    return response

@login_required
def download_import_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="book_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Author', 'Description', 'Price', 'Stock', 'Genres', 'Status'])
    writer.writerow(['Example Book', 'John Doe', 'Book description', '19.99', '10', 'Fiction, Mystery', 'draft'])
    
    return response

@login_required
def import_books(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'error': 'Please upload a CSV file'}, status=400)
    
    try:
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row in reader:
            try:
                # Create book instance
                book = Book(
                    title=row['Title'],
                    author=row['Author'],
                    description=row['Description'],
                    price=float(row['Price']),
                    stock=int(row['Stock']),
                    status=row['Status'].lower(),
                    seller=request.user
                )
                book.full_clean()  # Validate the model
                book.save()
                
                # Handle genres
                genre_names = [g.strip() for g in row['Genres'].split(',')]
                for genre_name in genre_names:
                    genre, _ = Genre.objects.get_or_create(name=genre_name)
                    book.genres.add(genre)
                
                success_count += 1
            except (ValueError, ValidationError, KeyError) as e:
                error_count += 1
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Imported {success_count} books successfully. {error_count} failed.',
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error processing file: {str(e)}'
        }, status=400)

@login_required
@require_POST
def bulk_action(request):
    action = request.POST.get('action')
    book_ids = request.POST.getlist('book_ids[]')
    
    if not action or not book_ids:
        return JsonResponse({'error': 'Action and book IDs are required'}, status=400)
    
    books = Book.objects.filter(id__in=book_ids, seller=request.user)
    
    try:
        if action == 'delete':
            books.delete()
            message = f'Successfully deleted {len(book_ids)} books'
        elif action == 'change_status':
            new_status = request.POST.get('status')
            if new_status not in dict(Book.STATUS_CHOICES):
                return JsonResponse({'error': 'Invalid status'}, status=400)
            books.update(status=new_status)
            message = f'Successfully updated status of {len(book_ids)} books'
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': message
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Error performing bulk action: {str(e)}'
        }, status=400)

@login_required
def book_analytics(request):
    books = Book.objects.filter(seller=request.user)
    
    # Basic statistics
    total_books = books.count()
    total_sales = books.aggregate(Sum('sale_count'))['sale_count__sum'] or 0
    total_revenue = books.aggregate(
        revenue=Sum('sale_count' * 'price', output_field=models.DecimalField())
    )['revenue'] or 0
    
    # Books by status
    status_counts = dict(books.values_list('status').annotate(count=Count('id')))
    
    # Top performing books
    top_books = books.order_by('-sale_count')[:5].values('title', 'sale_count', 'view_count')
    
    # Monthly sales trend (last 12 months)
    sales_trend = books.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        sales=Sum('sale_count')
    ).order_by('-month')[:12]
    
    # Genre performance
    genre_performance = Genre.objects.filter(
        book__seller=request.user
    ).annotate(
        book_count=Count('book', distinct=True),
        total_sales=Sum('book__sale_count'),
        avg_rating=Avg('book__review__rating')
    ).values('name', 'book_count', 'total_sales', 'avg_rating')
    
    context = {
        'total_books': total_books,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'status_counts': status_counts,
        'top_books': list(top_books),
        'sales_trend': list(sales_trend),
        'genre_performance': list(genre_performance)
    }
    
    return render(request, 'books/analytics.html', context) 