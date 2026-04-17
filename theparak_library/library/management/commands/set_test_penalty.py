from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from library.models import Borrowing


class Command(BaseCommand):
    help = 'Set a test penalty by adjusting both borrow and due dates'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to set penalty for')
        parser.add_argument('penalty_baht', type=int, help='Desired penalty in baht')

    def handle(self, *args, **options):
        username = options['username']
        penalty_baht = options['penalty_baht']
        
        try:
            # 1. Find user
            user = User.objects.get(username=username)
            self.stdout.write(f"Found user: {user.username}")
            
            # 2. Find active borrowing
            borrowing = Borrowing.objects.filter(student=user, is_returned=False).first()
            
            if not borrowing:
                self.stdout.write(self.style.ERROR(f"No active borrowing found for user {username}"))
                return
            
            self.stdout.write(f"Found borrowing: {borrowing.book.title}")
            
            # 3. Calculate time shifts
            # penalty = (days_overdue) * 5
            days_overdue = penalty_baht // 5
            
            # To be 'days_overdue' late, the due_date must be that many days in the past
            new_due_date = timezone.now() - timedelta(days=days_overdue)
            
            # The borrow_date should always be 7 days BEFORE the due_date
            new_borrow_date = new_due_date - timedelta(days=7)
            
            # 4. Update the database
            borrowing.borrow_date = new_borrow_date
            borrowing.due_date = new_due_date # <--- THIS IS THE FIX
            borrowing.save()
            
            # 5. Verification Math
            actual_days_borrowed = (timezone.now() - borrowing.borrow_date).days
            # Re-calculating penalty using your view logic
            current_penalty = (actual_days_borrowed - 7) * 5 if actual_days_borrowed > 7 else 0
            
            self.stdout.write(self.style.SUCCESS(f"\n✓ Time Travel Successful!"))
            self.stdout.write(f"Borrow Date: {borrowing.borrow_date.strftime('%d %b %Y')}")
            self.stdout.write(f"Due Date:    {borrowing.due_date.strftime('%d %b %Y')} (PAST)")
            self.stdout.write(f"Days Late:   {days_overdue}")
            self.stdout.write(f"Final Fine:  {current_penalty} baht")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))