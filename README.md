# 📚 Theparak Library - Django Digital Library System

A comprehensive digital library system for high schools built with **Django** and **MySQL**.

---

## 🚀 Project Overview
Theparak Library is a Django-based digital library management system designed specifically for high schools. It provides functionality for:
* **Managing book inventory**
* **Tracking book borrowing/returns**
* **Student reviews and ratings**
* **Author and category management**
* **Admin interface for library staff**

---

## 🗄️ Database Configuration
* **Database Name:** `theparak_library_db`
* **Database Engine:** MySQL (via XAMPP)
* **Host:** `localhost`
* **Port:** `3306`
* **User:** `root`
* **Password:** (empty)

### Core Library Tables
* `library_category`: Book categories
* `library_author`: Book authors
* `library_book`: Books in the library
* `library_book_authors`: Many-to-many relationship (Books & Authors)
* `library_borrowing`: Track book borrowing by students
* `library_review`: Student reviews for books

### Built-In Script for testing
* `create_catagory`: Generate catagory
* `generate_author`: Generate author
* `generate_student`: Generate Student
* `generate_book`: Generate book
* `set_test_penalty`: set penalty for testing


---

## 🛠️ Installation & Setup

### 1. Prerequisites
* Python 3.8+
* XAMPP with MySQL running

### 2. Initial Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
