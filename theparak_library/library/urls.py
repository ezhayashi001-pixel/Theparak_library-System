from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.index, name='index'),
    path('browse/', views.browse, name='browse'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('my-borrowings/', views.my_borrowings, name='my_borrowings'),
    path('borrow-tracking/', views.borrow_tracking, name='borrow_tracking'),
    path('member-list/', views.member_list, name='member_list'),
    path('api/create-member/', views.create_member, name='create_member'),
    path('api/delete-member/<int:member_id>/', views.delete_member, name='delete_member'),
    path('print-receipt/<int:borrowing_id>/', views.print_penalty_receipt, name='print_penalty_receipt'),
    path('mark-returned/<int:borrowing_id>/', views.mark_book_returned, name='mark_book_returned'),
    path('api/borrow-book/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('api/submit-review/', views.submit_review, name='submit_review'),
    path('add-book/', views.add_book, name='add_book'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-author/', views.add_author, name='add_author'),
    path('api/create-author/', views.create_author_api, name='create_author_api'),
    path('api/delete-book/<int:book_id>/', views.delete_book, name='delete_book'),
    path('api/delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('api/delete-author/<int:author_id>/', views.delete_author, name='delete_author'),
    path('api/toggle-favorite/<int:book_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('category/delete/<int:category_id>/', views.delete_category_cascade, name='delete_category_cascade'),
    path('confirm-payment/<int:borrowing_id>/', views.confirm_payment, name='confirm_payment'),
]
