from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import random

class Command(BaseCommand):
    help = 'Generate dummy students with specific SPU ID format'

    def add_arguments(self, parser):
        # เพิ่ม argument ให้เราเลือกจำนวนที่จะสร้างได้ตอนรันคำสั่ง
        parser.add_argument('total', type=int, help='Number of students to create')

    def handle(self, *args, **options):
        count = options['total']
        
        # Lists for random name generation
        first_names = ["Somchai", "Somsak", "Wichai", "Ananda", "Kitti", "Nattha", "Preecha", "Sunisa", "Thana", "Malee"]
        last_names = ["Sawatdee", "Rakthai", "Mongkol", "Jaidee", "Rattanapan", "Suksom", "Charoen", "Thongdee", "Boonyasit", "Silpa"]

        created_count = 0
        self.stdout.write(self.style.NOTICE(f"Starting to generate {count} students..."))

        while created_count < count:
            # Generate ID: 6621 followed by 3 random digits
            student_id = f"6621{random.randint(0, 999):03d}"
            
            # Check if username already exists
            if not User.objects.filter(username=student_id).exists():
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                
                # Create user
                user = User.objects.create_user(
                    username=student_id,
                    first_name=fname,
                    last_name=lname,
                    email=f"{fname.lower()}.{lname[:3].lower()}@spumail.net",
                    password="1234"
                )
                
                user.is_superuser = False
                user.is_staff = False
                user.save()
                
                self.stdout.write(f"Created: {student_id} - {fname} {lname}")
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"--- Successfully generated {count} students ---"))