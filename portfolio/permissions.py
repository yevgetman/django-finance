import os
from rest_framework import permissions

class GlobalHardcodedAPIKeyPermission(permissions.BasePermission):
    """
    Allows access only if a specific hardcoded API key is provided in the
    'Authorization' header.
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
