import re
from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        self.allowed_paths = {
            reverse('auth:main'),
            reverse('auth:login'),
            reverse('auth:signup'),
            reverse('auth:password_reset'),
            reverse('auth:logout')
        }

        self.allowed_patterns = [
            re.compile(r'^/auth/confirm_email/[^/]+/[^/]+/$'),
            re.compile(r'^/auth/reset/\d+/[^/]+/$'),
        ]

        self.allowed_view_names = {'confirm_email', 'reset_password_confirm'}

    def __call__(self, request):
        if not request.user.is_authenticated and not self.is_allowed_path(request):
            return redirect(reverse('auth:login'))

        return self.get_response(request)

    def is_allowed_path(self, request):
        path = request.path
        resolver_match = request.resolver_match

        if path in self.allowed_paths:
            return True

        if any(pattern.match(path) for pattern in self.allowed_patterns):
            return True

        if resolver_match and resolver_match.view_name in self.allowed_view_names:
            return True

        return False
