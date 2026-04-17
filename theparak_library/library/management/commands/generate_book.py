import datetime
import random
import os
from django.core.management.base import BaseCommand
from django.core.files import File # สำคัญมากสำหรับการจัดการไฟล์รูป
from django.conf import settings
from library.models import Book, Author, Category

class Command(BaseCommand):
    help = 'Generate dummy books with custom SN and random cover images'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of books to create')

    def handle(self, *args, **options):
        total = options['total']
        date_str = datetime.datetime.now().strftime("%d%m%Y")
        
        # 1. เตรียมรายชื่อไฟล์รูปจากโฟลเดอร์ media/book_covers
        cover_dir = os.path.join(settings.MEDIA_ROOT, 'book_covers')
        available_covers = []
        
        if os.path.exists(cover_dir):
            available_covers = [f for f in os.listdir(cover_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        categories = list(Category.objects.all())
        authors = list(Author.objects.all())

        if not categories or not authors:
            self.stdout.write(self.style.ERROR('Error: Please generate Category and Author first!'))
            return

        created_count = 0
        for i in range(1, total + 1):
            book_id_str = str(i).zfill(3)
            new_sn = f"{date_str}{book_id_str}"
            
            cat = random.choice(categories)
            auth = random.choice(authors)
            
            book = Book.objects.create(
                title=f'Sample Book {i}',
                serial_number=new_sn,
                category=cat,
                description=f'This is a generated description for book {i}',
                publication_date=datetime.date.today(),
                is_available=True
            )
            
            # 2. สุ่มใส่รูปหน้าปก (ถ้ามีไฟล์ในโฟลเดอร์)
            if available_covers:
                random_cover = random.choice(available_covers)
                cover_path = os.path.join(cover_dir, random_cover)
                # ใช้ File() ของ Django เพื่อบันทึกลงในฟิลด์ ImageField
                with open(cover_path, 'rb') as f:
                    book.cover_image.save(random_cover, File(f), save=True)

            book.authors.add(auth)
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {book.title} (SN: {new_sn}) with image: {random_cover if available_covers else "None"}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} books with random covers!'))