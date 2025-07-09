import os
from rest_framework import permissions


class GlobalHardcodedAPIKeyPermission(permissions.BasePermission):
    """
    Custom permission to check for a global API Authorization key.
    This key must be provided in the Authorization header for all API requests.
    """
    message = 'Invalid or missing global API Authorization key.'

    def has_permission(self, request, view):
        expected_key = os.getenv('AUTH_API_KEY')
        if not expected_key:
            # If the AUTH_API_KEY is not set in the environment, deny all access
            # to prevent accidental open access.
            return False

        provided_key = request.headers.get('Authorization')

        if not provided_key:
            return False
        
        return provided_key == expected_key


class IsAuthenticatedOrAnonymous(permissions.BasePermission):
    """
    Custom permission that allows access to both authenticated users and anonymous users,
    as long as they have passed the global API key check.
    
    This replaces the default IsAuthenticated permission to allow anonymous API access.
    """
    
    def has_permission(self, request, view):
        # Allow both authenticated users and anonymous users
        # The global API key check is handled by GlobalHardcodedAPIKeyPermission
        return True
