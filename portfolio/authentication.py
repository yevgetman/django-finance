from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that authenticates users via API key in the Authentication header.
    
    Expected header format: Authentication: <api_key>
    
    If no Authentication header is provided, the user will be treated as anonymous
    but the request can still proceed if other permissions allow it.
    """
    
    def authenticate(self, request):
        # Check for Authentication header (optional for user identification)
        auth_header = request.headers.get('Authentication')
        
        if not auth_header:
            # No Authentication header - treat as anonymous user
            # Return None to allow other authenticators or anonymous access
            return None

        # auth_header should be just the API key value
        api_key = auth_header.strip()
        
        if not api_key:
            msg = _('Invalid API key header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        
        return self.authenticate_credentials(api_key)
    
    def authenticate_credentials(self, api_key):
        """
        Authenticate the API key and return the associated user.
        """
        try:
            user = User.objects.get(api_key=api_key, is_api_active=True, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid API key.'))
        
        # Update last access time
        user.update_last_access()
        
        return (user, api_key)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'ApiKey'


class AnonymousAPIAuthentication(authentication.BaseAuthentication):
    """
    Authentication class that always returns an anonymous user.
    This ensures that requests without Authentication headers are treated as anonymous
    rather than unauthenticated, allowing them to pass through to permission checks.
    """
    
    def authenticate(self, request):
        # Always return anonymous user if no other authentication succeeded
        return (AnonymousUser(), None)
