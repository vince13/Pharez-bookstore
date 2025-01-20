from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('book/<slug:slug>/', views.book_detail, name='book_detail'),
    path('book/<slug:slug>/review/', views.add_review, name='add_review'),
    path('add/', views.add_book, name='add_book'),
    path('book/<slug:slug>/edit/', views.edit_book, name='edit_book'),
    path('book/<slug:slug>/delete/', views.delete_book, name='delete_book'),
    path('my-books/', views.my_books, name='my_books'),
    
    # Import/Export URLs
    path('export/', views.export_books, name='export_books'),
    path('import/', views.import_books, name='import_books'),
    path('download-template/', views.download_import_template, name='download_template'),
    
    # Bulk Actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    
    # Analytics
    path('analytics/', views.book_analytics, name='analytics'),
] 