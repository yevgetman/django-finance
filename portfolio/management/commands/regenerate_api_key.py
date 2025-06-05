from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Regenerate API key for an existing user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
            old_key = user.api_key
            new_key = user.regenerate_api_key()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully regenerated API key for user "{username}"')
            )
            self.stdout.write(f'User ID: {user.id}')
            self.stdout.write(f'Old API Key: {old_key[:16]}...')
            self.stdout.write(f'New API Key: {new_key}')
            
            self.stdout.write(
                self.style.WARNING('\nIMPORTANT: Save the new API key securely. The old key is now invalid.')
            )

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" does not exist.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
