from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that authenticates users via API key in the Authorization header.
    
    Expected header format: Authorization: ApiKey <api_key>
    """
    keyword = 'ApiKey'
    
    def authenticate(self, request):
        # Changed from 'Authorization' to 'Authentication'
        auth_header = request.headers.get('Authentication')
        
        if not auth_header:
            # No Authentication header, allow other mechanisms or AllowAny
            return None

        # auth_header is already a string, no need for .decode('utf-8')
        auth = auth_header.split()
        
        if len(auth) == 0 or auth[0].lower() != self.keyword.lower():
            # Header is present but not using the 'ApiKey' scheme, or empty.
            # Let other authenticators handle it, or if none, permissions will decide.
            return None
        
        if len(auth) == 1:
            msg = _('Invalid API key header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid API key header. API key string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)
        
        api_key = auth[1]
        
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
        return self.keyword
