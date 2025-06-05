from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'List all API users and their status'

    def add_arguments(self, parser):
        parser.add_argument('--active-only', action='store_true', help='Show only active users')
        parser.add_argument('--show-keys', action='store_true', help='Show partial API keys (first 16 chars)')

    def handle(self, *args, **options):
        active_only = options.get('active_only', False)
        show_keys = options.get('show_keys', False)

        users = User.objects.all()
        if active_only:
            users = users.filter(is_active=True, is_api_active=True)

        users = users.order_by('-created_at')

        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found.'))
            return

        self.stdout.write(f'Found {users.count()} user(s):')
        self.stdout.write('-' * 80)

        for user in users:
            status_indicators = []
            if user.is_active:
                status_indicators.append('ACTIVE')
            else:
                status_indicators.append('INACTIVE')
                
            if user.is_api_active:
                status_indicators.append('API_ACTIVE')
            else:
                status_indicators.append('API_INACTIVE')

            status = ' | '.join(status_indicators)
            
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Status: {status}')
            self.stdout.write(f'Created: {user.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            
            if user.last_api_access:
                self.stdout.write(f'Last API Access: {user.last_api_access.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                self.stdout.write('Last API Access: Never')
                
            if show_keys:
                self.stdout.write(f'API Key: {user.api_key[:16]}...')
                
            self.stdout.write('-' * 80)
