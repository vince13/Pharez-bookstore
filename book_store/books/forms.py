from django import forms
from .models import Book, Review

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'price', 'stock', 'cover_image', 'genres', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter author name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter book description'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'accept': 'image/*'
            }),
            'genres': forms.CheckboxSelectMultiple(),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'genres': 'Select Genres (Choose at least one)',
            'status': 'Book Status'
        }
        help_texts = {
            'genres': 'Select all applicable genres for your book',
            'status': 'Draft: Only you can see the book. Published: Available for purchase. Archived: Hidden from the store.'
        }

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            if cover_image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
            return cover_image
        return None

    def clean_genres(self):
        genres = self.cleaned_data.get('genres')
        if not genres:
            raise forms.ValidationError("Please select at least one genre")
        return genres

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment'] 