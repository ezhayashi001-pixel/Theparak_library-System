from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from datetime import timedelta
from .models import Book, Category, Author, Borrowing, Favorite, Payment
from .forms import BookForm, CategoryForm, AuthorForm

# Create your views here.

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('library:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('library:index')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'library/login.html')


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('library:index')


@login_required(login_url='library:login')
def user_profile(request):
    """User profile view"""
    context = {
        'user': request.user,
    }
    return render(request, 'library/profile.html', context)


@login_required(login_url='library:login')
def my_borrowings(request):
    """View all borrowings for current user"""
    # Get all borrowings for the current user
    borrowings = Borrowing.objects.filter(student=request.user).order_by('-borrow_date')
    
    # Separate active and returned borrowings
    active_borrowings = borrowings.filter(is_returned=False)
    returned_borrowings = borrowings.filter(is_returned=True)
    
    # 1. จัดการรายการที่ยังไม่คืน (Active)
    for borrowing in active_borrowings:
        # คำนวณจำนวนวันที่ยืมมาจนถึงปัจจุบัน
        days_borrowed = (timezone.now() - borrowing.borrow_date).days
        
        penalty = 0
        # กฎคือยืมได้ 7 วัน ถ้าเกินกว่านั้นเริ่มปรับ
        if days_borrowed > 7:
            penalty = (days_borrowed - 7) * 5
            
        borrowing.days_borrowed = days_borrowed
        borrowing.penalty = penalty
        borrowing.is_overdue = days_borrowed > 7
    
    # 2. จัดการรายการที่คืนแล้ว (Returned)
    for borrowing in returned_borrowings:
        # ป้องกัน Error: ตรวจสอบว่ามี return_date หรือไม่ 
        # ถ้าไม่มี (เพราะเราลืมเซ็ตตอนจ่ายเงิน) ให้ใช้ timezone.now() แทนไปก่อน
        if borrowing.return_date:
            days_borrowed = (borrowing.return_date - borrowing.borrow_date).days
        else:
            days_borrowed = (timezone.now() - borrowing.borrow_date).days
            
        borrowing.days_borrowed = max(days_borrowed, 0) # ป้องกันค่าติดลบ
    
    context = {
        'active_borrowings': active_borrowings,
        'returned_borrowings': returned_borrowings,
    }
    return render(request, 'library/my_borrowings.html', context)


def index(request):
    """Home page view for both Students and Admins"""
    from django.db.models import Q
    from django.utils import timezone

    # 1. รับค่าการค้นหา
    book_search = request.GET.get('book_search', '')

    # 2. จัดการเรื่องการค้นหาหนังสือ
    # สร้าง QuerySet ตั้งต้น
    books = Book.objects.all().order_by('-id')
    
    if book_search:
        books = books.filter(
            Q(title__icontains=book_search) |
            Q(description__icontains=book_search) |
            Q(authors__first_name__icontains=book_search) |
            Q(authors__last_name__icontains=book_search) |
            Q(serial_number__icontains=book_search) |
            Q(category__name__icontains=book_search)
        ).distinct()

    # 3. เตรียม Context
    context = {
        'latest_books': books, # <--- ตรวจสอบว่าใน HTML ใช้ชื่อนี้ใน {% for %}
        'book_search': book_search,
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'total_categories': Category.objects.count(),
    }

    if request.user.is_authenticated:
        if request.user.is_superuser:
            # --- สำหรับ ADMIN ---
            context.update({
                'total_users': User.objects.filter(is_superuser=False).count(),
                'active_borrows': Borrowing.objects.filter(is_returned=False).count(),
                'overdue_count': Borrowing.objects.filter(is_returned=False, due_date__lt=timezone.now()).count(),
                'total_categories_list': Category.objects.all(),
                'total_authors_list': Author.objects.all(),
            })
            # มั่นใจว่าเราส่ง 'latest_books' ที่ถูก filter แล้วไปที่นี่
            return render(request, 'library/admin_dashboard.html', context)
        
        else:
            # --- สำหรับ STUDENT ---
            overdue_qs = Borrowing.objects.filter(
                student=request.user,
                due_date__lt=timezone.now(),
                is_returned=False
            )
            if overdue_qs.exists():
                first_overdue = overdue_qs.order_by('due_date').first()
                days_late = (timezone.now().date() - first_overdue.due_date.date()).days
                days_to_display = max(days_late, 1)
                context['overdue_alert'] = {
                    'book_title': first_overdue.book.title,
                    'days_late': days_to_display,
                    'penalty': days_to_display * 5
                }
    
    return render(request, 'library/index.html', context)


def browse(request):
    """Browse books view with filtering and search"""
    books = Book.objects.all()
    categories = Category.objects.all()
    authors = Author.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(authors__first_name__icontains=search_query) |
            Q(authors__last_name__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(serial_number__icontains=search_query)
        ).distinct()
    
    # Category filter
    category_id = request.GET.get('category', '')
    selected_category = None
    selected_category_name = None
    if category_id:
        selected_category = category_id
        try:
            selected_category_obj = Category.objects.get(id=category_id)
            selected_category_name = selected_category_obj.name
            books = books.filter(category__id=category_id)
        except Category.DoesNotExist:
            pass
    
    # Availability filter
    availability = request.GET.get('availability', '')
    if availability == 'available':
        books = books.filter(is_available=True)
    elif availability == 'unavailable':
        books = books.filter(is_available=False)
    
    # Sorting / Favorites filter
    sort = request.GET.get('sort', '-created_at')
    if sort == 'favorites':
        if request.user.is_authenticated:
            favorite_book_ids = Favorite.objects.filter(user=request.user).values_list('book_id', flat=True)
            books = books.filter(id__in=favorite_book_ids).order_by('-created_at')
        else:
            books = books.none()
    else:
        books = books.order_by(sort)
    
    # Check if any filters are applied
    has_filters = bool(search_query or category_id or availability or sort == 'favorites')
    
    # Get user's favorite books for display
    user_favorite_ids = []
    if request.user.is_authenticated:
        user_favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('book_id', flat=True))
    
    context = {
        'books': books,
        'categories': categories,
        'authors': authors,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_category_name': selected_category_name,
        'availability': availability,
        'sort': sort,
        'has_filters': has_filters,
        'user_favorite_ids': user_favorite_ids,
    }
    
    return render(request, 'library/browse.html', context)


def is_superuser(user):
    """Check if user is a superuser"""
    return user.is_superuser

from django.db.models import Q # มั่นใจว่ามีบรรทัดนี้ที่หัวไฟล์นะ

def borrow_tracking(request):
    """Borrow tracking view for superusers with search functionality"""
    # 1. Check permission
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('library:index')
    
    # 2. Get search query
    search_query = request.GET.get('search', '')

    # 3. เริ่มต้นดึงข้อมูลนักเรียน (ดึงมาแค่รอบเดียวพอ)
    users = User.objects.filter(is_superuser=False).order_by('username')
    
    # 4. ถ้ามีการค้นหา ให้กรองข้อมูลในตัวแปร users เดิม
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )

    student_data = []
    
    # 5. วนลูปจากตัวแปร users ที่ถูกกรองเรียบร้อยแล้ว
    for user in users:
        # Get active borrowing (not returned)
        active_borrowing = Borrowing.objects.filter(
            student=user,
            is_returned=False
        ).first()
        
        # Get all borrowing history
        all_borrowings = Borrowing.objects.filter(student=user).order_by('-borrow_date')
        
        if active_borrowing:
            # Calculate days borrowed
            days_borrowed = (timezone.now() - active_borrowing.borrow_date).days
            
            # Calculate penalty (5 baht per day after 7 days)
            penalty = 0
            if days_borrowed > 7:
                penalty = (days_borrowed - 7) * 5
            
            status = 'Borrowing'
        else:
            days_borrowed = 0
            penalty = 0
            status = 'None'
        
        student_data.append({
            'user': user,
            'status': status,
            'days_borrowed': days_borrowed,
            'penalty': penalty,
            'active_borrowing': active_borrowing,
            'all_borrowings': all_borrowings,
        })
    
    # 6. ส่งค่ากลับไปที่ HTML
    context = {
        'student_data': student_data,
        'search_query': search_query, # ส่งตัวนี้กลับไปด้วย เพื่อให้ช่อง Search ยังโชว์คำที่พิมพ์ค้างไว้
    }

    return render(request, 'library/borrow_tracking.html', context)


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def member_list(request):
    """Member list view for superusers to manage library members"""
    # Get all non-superuser members (students)
    members = User.objects.filter(is_superuser=False).order_by('username')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'username')
    members = members.order_by(sort_by)
    
    # Calculate member statistics
    total_members = User.objects.filter(is_superuser=False).count()
    active_borrowers = Borrowing.objects.filter(is_returned=False).values('student').distinct().count()
    total_penalties = 0
    
    for user in User.objects.filter(is_superuser=False):
        active_borrowing = Borrowing.objects.filter(
            student=user,
            is_returned=False
        ).first()
        
        if active_borrowing:
            days_borrowed = (timezone.now() - active_borrowing.borrow_date).days
            if days_borrowed > 7:
                total_penalties += (days_borrowed - 7) * 5
    
    context = {
        'members': members,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_members': total_members,
        'active_borrowers': active_borrowers,
        'total_penalties': total_penalties,
    }
    
    return render(request, 'library/member_list.html', context)


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def create_member(request):
    """Create a new member (superuser only)"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            
            # Validation
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Student ID and password are required.'
                })
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Student ID "{username}" already exists.'
                })
            
            if email and User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Email "{email}" is already registered.'
                })
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Member "{username}" has been created successfully!'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating member: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def delete_member(request, member_id):
    """Delete a member (superuser only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method. Only POST is allowed.'
        })
    
    try:
        member = User.objects.get(id=member_id)
        
        # Prevent deletion of superusers
        if member.is_superuser:
            messages.error(request, 'Cannot delete an admin user.')
            return redirect('library:member_list')
        
        active_borrowings = Borrowing.objects.filter(student=member, is_returned=False)
        if active_borrowings.exists():
            messages.error(request, f'Cannot delete member "{member.username}" because they have active borrowings.')
            return redirect('library:member_list')
        
        member_name = f"{member.get_full_name()} ({member.username})"
        member.delete()
        messages.success(request, f'Member {member_name} has been deleted successfully!')
        return redirect('library:member_list')
    except User.DoesNotExist:
        messages.error(request, 'Member not found.')
        return redirect('library:member_list')
    except Exception as e:
        messages.error(request, f'Error deleting member: {str(e)}')
        return redirect('library:member_list')


@login_required(login_url='library:login')
@transaction.atomic
def borrow_book(request, book_id):
    """Borrow a book (authenticated users only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })
    
    try:
        # Get fresh book object from database
        book = Book.objects.select_for_update().get(id=book_id)
        
        # Check if user already has an active borrowing of this book
        existing_borrow = Borrowing.objects.filter(
            student=request.user,
            book=book,
            is_returned=False
        ).exists()
        
        if existing_borrow:
            return JsonResponse({
                'success': False,
                'message': 'You already have this book checked out.'
            })
        
        # Check if ANY user has an active borrowing of this book
        any_active_borrow = Borrowing.objects.filter(
            book=book,
            is_returned=False
        ).exists()
        
        if any_active_borrow:
            return JsonResponse({
                'success': False,
                'message': 'This book is currently not available.'
            })
        
        # Create borrowing record
        due_date = timezone.now() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            student=request.user,
            book=book,
            due_date=due_date,
            is_returned=False
        )
        
        # Mark book as unavailable
        book.is_available = False
        book.save()
        
        return JsonResponse({
            'success': True,
            'message': f'You have successfully borrowed "{book.title}". Due date: {due_date.strftime("%d %b %Y")}'
        })
    except Book.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Book not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required(login_url='library:login')
def submit_review(request):
    """Submit a review for a book (authenticated users only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })
    
    try:
        import json
        data = json.loads(request.body)
        
        book_id = data.get('book_id')
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not book_id or not rating:
            return JsonResponse({
                'success': False,
                'message': 'Book ID and rating are required.'
            })
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'Rating must be between 1 and 5.'
                })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid rating value.'
            })
        
        book = Book.objects.get(id=book_id)
        
        # Check if user already reviewed this book
        from .models import Review
        review, created = Review.objects.update_or_create(
            book=book,
            student=request.user,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )
        
        if created:
            message = 'Your review has been submitted successfully!'
        else:
            message = 'Your review has been updated successfully!'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
    
    except Book.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Book not found.'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def print_penalty_receipt(request, borrowing_id):
    """Print penalty receipt for a student (superuser only)"""
    try:
        borrowing = Borrowing.objects.get(id=borrowing_id, is_returned=False)
        
        # Calculate penalty
        days_borrowed = (timezone.now() - borrowing.borrow_date).days
        penalty = 0
        if days_borrowed > 7:
            penalty = (days_borrowed - 7) * 5
        
        context = {
            'borrowing': borrowing,
            'days_borrowed': days_borrowed,
            'penalty': penalty,
            'current_date': timezone.now(),
        }
        
        return render(request, 'library/penalty_receipt.html', context)
    except Borrowing.DoesNotExist:
        messages.error(request, 'Borrowing record not found.')
        return redirect('library:borrow_tracking')


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def mark_book_returned(request, borrowing_id):
    """Mark a book as returned (superuser only)"""
    try:
        borrowing = Borrowing.objects.get(id=borrowing_id, is_returned=False)
        borrowing.is_returned = True
        borrowing.return_date = timezone.now()
        borrowing.save()
        
        # Mark book as available again
        book = borrowing.book
        book.is_available = True
        book.save()
        
        messages.success(request, f'Book "{borrowing.book.title}" has been marked as returned.')
        return redirect('library:borrow_tracking')
    except Borrowing.DoesNotExist:
        messages.error(request, 'Borrowing record not found.')
        return redirect('library:borrow_tracking')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('library:borrow_tracking')


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def add_book(request):
    """Add a new book view (superuser only)"""
    if request.method == 'POST':
        # Get the comma-separated author IDs from the hidden field
        author_ids_str = request.POST.get('authors', '')
        
        # Convert to list of integers if not empty
        if author_ids_str:
            author_ids = [int(id) for id in author_ids_str.split(',') if id.strip()]
        else:
            author_ids = []
        
        # Create a copy of POST data and modify the authors field
        post_data = request.POST.copy()
        post_data.setlist('authors', author_ids)
        
        form = BookForm(post_data, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            # Generate serial number
            book.serial_number = book.generate_serial_number()
            book.save()
            form.save_m2m()  # Save the many-to-many relationship
            messages.success(request, f'Book "{book.title}" has been added successfully! Serial Number: {book.serial_number}')
            return redirect('library:index')
        else:
            messages.error(request, 'Error adding the book. Please check the form.')
    else:
        form = BookForm()
    
    context = {
        'form': form,
        'title': 'Add New Book'
    }
    return render(request, 'library/add_book.html', context)


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def add_category(request):
    """Add a new category view (superuser only)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" has been added successfully!')
            return redirect('library:index')
        else:
            messages.error(request, 'Error adding the category. Please check the form.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Add New Category'
    }
    return render(request, 'library/add_category.html', context)


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def add_author(request):
    """Add a new author view (superuser only)"""
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Author "{author.first_name} {author.last_name}" has been added successfully!')
            return redirect('library:index')
        else:
            messages.error(request, 'Error adding the author. Please check the form.')
    else:
        form = AuthorForm()
    
    context = {
        'form': form,
        'title': 'Add New Author'
    }
    return render(request, 'library/add_author.html', context)


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def delete_book(request, book_id):
    """Delete a book (superuser only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method. Only POST is allowed.'
        })
    
    try:
        book = Book.objects.get(id=book_id)
        borrow_books = Borrowing.objects.filter(book=book, is_returned=False)
        if borrow_books.exists():
            messages.error(request, f'Cannot delete book "{book.title}" because it is currently borrowed by a student.')
            return redirect('library:index')
        book_title = book.title  # Save title before deleting
        book.delete()
        messages.success(request, f'Book "{book_title}" has been deleted successfully!')
        return redirect('library:index')
    except Book.DoesNotExist:
        messages.error(request, 'Book not found.')
        return redirect('library:index')
    except Exception as e:
        messages.error(request, f'Error deleting book: {str(e)}')
        return redirect('library:index')


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def delete_category(request, category_id):
    """Delete a category (superuser only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method. Only POST is allowed.'
        })
    
    try:
        category = Category.objects.get(id=category_id)
        borrow_books = category.books.filter(is_available=False)
        if borrow_books.exists():
            messages.error(request, f'Cannot delete category "{category.name}" because it has books that are currently borrowed.')
            return redirect('library:index')
        category_name = category.name  # Save name before deleting
        category.delete()
        messages.success(request, f'Category "{category_name}" has been deleted successfully!')
        return redirect('library:index')
    except Category.DoesNotExist:
        messages.error(request, 'Category not found.')
        return redirect('library:index')
    except Exception as e:
        messages.error(request, f'Error deleting category: {str(e)}')
        return redirect('library:index')


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def delete_author(request, author_id):
    """Delete an author and their associated books (superuser only)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method. Only POST is allowed.'
        })
    
    try:
        author = Author.objects.get(id=author_id)
        
        # 1. เช็คก่อนว่ามีหนังสือเล่มไหนของคนแต่งคนนี้ที่ถูกยืมอยู่ไหม
        borrowed_books = author.books.filter(is_available=False)

        if borrowed_books.exists():
            messages.error(request, f'ไม่สามารถลบผู้แต่ง "{author.first_name} {author.last_name}" ได้ เนื่องจากมีหนังสือที่ถูกยืมอยู่ในขณะนี้')
            return redirect('library:index')
        
        # 2. ดึงรายชื่อหนังสือทั้งหมดของผู้แต่งคนนี้ (ที่ว่างอยู่) เพื่อเตรียมลบ
        books_to_delete = author.books.all()
        author_name = f"{author.first_name} {author.last_name}"
        
        # 3. ลบหนังสือทิ้งก่อน
        books_count = books_to_delete.count()
        books_to_delete.delete() 
        
        # 4. ค่อยลบผู้แต่ง
        author.delete()
        
        messages.success(request, f'ลบผู้แต่ง "{author_name}" และหนังสือที่เกี่ยวข้องจำนวน {books_count} เล่มเรียบร้อยแล้ว!')
        return redirect('library:index')

    except Author.DoesNotExist:
        messages.error(request, 'ไม่พบข้อมูลผู้แต่ง')
        return redirect('library:index')
    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect('library:index')
    
    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_category_cascade(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category_name = category.name
        # This will delete the category AND all related books because of models.CASCADE
        category.delete() 
        messages.success(request, f'ลบหมวดหมู่ "{category_name}" และหนังสือทั้งหมดในหมวดหมู่นี้เรียบร้อยแล้ว')
    return redirect('library:index')


@login_required(login_url='library:login')
@user_passes_test(is_superuser, login_url='library:index')
def create_author_api(request):
    """API endpoint to create a new author (superuser only)"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            bio = data.get('bio', '').strip()
            
            if not first_name or not last_name:
                return JsonResponse({
                    'success': False,
                    'message': 'First name and last name are required.'
                })
            
            # Create the author
            author = Author.objects.create(
                first_name=first_name,
                last_name=last_name,
                bio=bio
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Author "{author.first_name} {author.last_name}" created successfully!',
                'author_id': author.id,
                'author_name': f'{author.first_name} {author.last_name}'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })
    """API endpoint to create a new author (superuser only)"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            bio = data.get('bio', '').strip()
            
            if not first_name or not last_name:
                return JsonResponse({
                    'success': False,
                    'message': 'First name and last name are required.'
                })
            
            # Create the author
            author = Author.objects.create(
                first_name=first_name,
                last_name=last_name,
                bio=bio
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Author "{author.first_name} {author.last_name}" created successfully!',
                'author_id': author.id,
                'author_name': f'{author.first_name} {author.last_name}'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required(login_url='library:login')
def toggle_favorite(request, book_id):
    """Toggle favorite status for a book (works for both admin and user)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })
    
    try:
        book = Book.objects.get(id=book_id)
        
        # Check if already favorited
        favorite = Favorite.objects.filter(user=request.user, book=book).first()
        
        if favorite:
            # Remove from favorites
            favorite.delete()
            is_favorited = False
            message = f'Removed "{book.title}" from favorites'
        else:
            # Add to favorites
            Favorite.objects.create(user=request.user, book=book)
            is_favorited = True
            message = f'Added "{book.title}" to favorites'
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'message': message
        })
    
    except Book.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Book not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def confirm_payment(request, borrowing_id):
    if request.method == 'POST' and request.user.is_superuser:
        borrowing = Borrowing.objects.get(id=borrowing_id)
        
        # แก้ไขบรรทัดนี้ครับ
        days_late = (timezone.now().date() - borrowing.due_date.date()).days
        penalty = max(days_late * 5, 0)
        
        # บันทึกการชำระเงิน
        Payment.objects.create(
            borrowing=borrowing,
            student=borrowing.student,
            amount=penalty
        )
        
        # คืนหนังสือ
        borrowing.is_returned = True
        borrowing.return_date = timezone.now()
        borrowing.save()

        book = borrowing.book
        book.is_available = True
        book.save()
        
        messages.success(request, f"บันทึกการชำระเงินเรียบร้อยแล้ว")
        return redirect('library:index') # หรือหน้า dashboard