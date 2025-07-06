from django.shortcuts import redirect
from django.conf import settings

class RedirectAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated users
        if request.user.is_authenticated and request.path in ['/shop-admin','/shop-admin/']:
            return redirect('index')  # or 'student_dashboard' based on user

        if not request.user.is_authenticated and request.path in ['/shop-admin/dashboard', '/shop-admin/dashboard/']:
            return redirect('login')

        return self.get_response(request)