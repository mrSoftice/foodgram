from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Allow read-only access to anyone, but modifications only to the author.

    - SAFE_METHODS (GET, HEAD, OPTIONS) are allowed for any request.
    - POST is allowed for authenticated users (so they can create recipes).
    - PUT/PATCH/DELETE are allowed only if the request user is the object's author.
    """

    def has_permission(self, request, view):
        # Allow anyone to list/retrieve (safe methods)
        if request.method in SAFE_METHODS:
            return True
        # Allow authenticated users to create
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        # For other methods (PUT, PATCH, DELETE) we defer to has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        # Safe methods already allowed in has_permission
        if request.method in SAFE_METHODS:
            return True
        # For modifications, require object has 'author' and that it's the request user
        author = getattr(obj, 'author', None)
        if author is None:
            return False
        return (
            request.user
            and request.user.is_authenticated
            and author == request.user
        )
