from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a new user with API key for portfolio analysis access'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('email', type=str, help='Email address for the new user')
        parser.add_argument('--first-name', type=str, help='First name of the user')
        parser.add_argument('--last-name', type=str, help='Last name of the user')
        parser.add_argument('--inactive', action='store_true', help='Create user as inactive')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        is_active = not options.get('inactive', False)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists.')
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" already exists.')
            )
            return

        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
                is_api_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created user "{username}"')
            )
            self.stdout.write(f'User ID: {user.id}')
            self.stdout.write(f'API Key: {user.api_key}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Active: {user.is_active}')
            self.stdout.write(f'API Active: {user.is_api_active}')
            
            self.stdout.write(
                self.style.WARNING('\nIMPORTANT: Save the API key securely. It cannot be retrieved again.')
            )

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
