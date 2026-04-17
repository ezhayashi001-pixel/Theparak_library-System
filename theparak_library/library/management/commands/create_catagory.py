import random
from django.core.management.base import BaseCommand
from library.models import Category

class Command(BaseCommand):
    help = 'สร้างหมวดหมู่หนังสือแบบสุ่ม (ภาษาไทย)'

    def add_arguments(self, parser):
        # คุณสามารถระบุจำนวนที่ต้องการสร้างได้ เช่น python manage.py generate_categories 5
        parser.add_argument('total', type=int, help='จำนวนหมวดหมู่ที่ต้องการสร้าง')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        
        # รายชื่อหมวดหมู่ภาษาไทยที่น่าสนใจ
        category_names = [
            "เทคโนโลยีและคอมพิวเตอร์", "วรรณกรรมเยาวชน", "ประวัติศาสตร์โลก", 
            "การพัฒนาตนเอง", "นิยายวิทยาศาสตร์", "บริหารธุรกิจ", 
            "ศิลปะและการออกแบบ", "ภาษาศาสตร์", "วิทยาศาสตร์ทั่วไป",
            "ภูมิศาสตร์และการท่องเที่ยว", "สุขภาพและกายภาพ", "กฎหมายเบื้องต้น"
        ]

        created_count = 0
        
        # วนลูปสร้างตามจำนวนที่กำหนด
        for name in category_names[:total]:
            # ใช้ get_or_create เพื่อป้องกันชื่อซ้ำกันแล้ว Error
            category, created = Category.objects.get_or_create(name=name)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'สร้างหมวดหมู่เรียบร้อย: {name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'หมวดหมู่ "{name}" มีอยู่ในระบบแล้ว'))

        self.stdout.write(self.style.SUCCESS(f'--- สรุป: สร้างหมวดหมู่ใหม่ทั้งหมด {created_count} รายการ ---'))