from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

class Category(models.Model):
    """Book categories for easy browsing"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Author(models.Model):
    """Authors of books in the library"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['last_name', 'first_name']


class Book(models.Model):
    """Books available in the digital library"""
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    serial_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField()
    publication_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def generate_serial_number(self):
        """Generate a unique serial number based on date and sequence"""
        today = timezone.now().date()
        date_part = today.strftime('%d%m%Y')
        
        # Count books created today
        books_today = Book.objects.filter(
            created_at__date=today
        ).count()
        
        # Generate sequence number (001, 002, etc.)
        sequence = str(books_today + 1).zfill(3)
        
        return f"{date_part}{sequence}"
    
    class Meta:
        ordering = ['-created_at']


class Borrowing(models.Model):
    """Track book borrowing by students"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    borrow_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField()
    is_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.username} - {self.book.title}"
    
    class Meta:
        ordering = ['-borrow_date']


class Review(models.Model):
    """Student reviews for books"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.book.title} - {self.rating} stars"
    
    class Meta:
        unique_together = ('book', 'student')
        ordering = ['-created_at']


class Favorite(models.Model):
    """Track favorite books for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
    
    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

class Payment(models.Model):
    borrowing = models.OneToOneField('Borrowing', on_delete=models.CASCADE, related_name='payment')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Completed')

    def __str__(self):
        return f"Payment {self.amount} by {self.student.username}"