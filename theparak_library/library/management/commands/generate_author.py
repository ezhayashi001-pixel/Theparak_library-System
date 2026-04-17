import random
import string
from django.core.management.base import BaseCommand
from library.models import Author

class Command(BaseCommand):
    help = 'Generate dummy authors without biography'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of authors to be created')

    def handle(self, *args, **options):
        total = options['total']
        
        first_names = ['Kitti', 'Wichai', 'Somsak', 'Ananda', 'Malee', 'Sunisa', 'Nattha', 'Somchai', 'Thana', 'Piti', 'Kamon', 'Arun', 'Chai']
        last_names = ['Mongkol', 'Thongdee', 'Rakthai', 'Suksant', 'Charoen', 'Suksom', 'Rattanapan', 'Silpa', 'Jaidee', 'Phopa']

        created_count = 0
        
        for i in range(total):
            f_name = random.choice(first_names)
            l_name = random.choice(last_names)
            
            # ป้องกันชื่อซ้ำ (เพราะลบ Bio ออกแล้วเหลือแค่ชื่อ-นามสกุล)
            if Author.objects.filter(first_name=f_name, last_name=l_name).exists():
                f_name = f"{f_name}-{random.choice(string.ascii_uppercase)}"
            
            Author.objects.create(
                first_name=f_name,
                last_name=l_name
                # ลบ biography=... ออกแล้ว
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} authors!'))