from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string

from .models import User
from .forms import SignUpForm, LoginForm, PasswordResetForm, PasswordResetRequestForm
from .celery_tasks import send_confirmation_email as send_confirmation_email_celery

class MainPage(View):
    template_name = 'custom_auth/main.html'
    context_object_name = 'main'

    def get(self, request, *args, **kwargs):
        context = {
            self.context_object_name: "Welcome to the Main Page!"
        }
        return render(request, self.template_name, context)

class SignUpView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'custom_auth/signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'A user with the same email address already exists.')
                return redirect('auth:signup')

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()
            user.send_confirmation_email(request)

            return render(request, 'custom_auth/email_verification_prompt.html', {'user': user})

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.info(request, error)
                    return redirect('auth:signup')

        return render(request, 'custom_auth/signup.html', {'form': form})

class ConfirmEmailView(View):
    def get(self, request, uid, token):

        user = get_object_or_404(User, uid=uid)


        if user.confirmation_token == token:
            if not user.email_verified:

                user.email_verified = True
                user.confirmation_token = None
                user.save(update_fields=['email_verified', 'confirmation_token'])

                return render(request, 'custom_auth/email_verified.html')
            else:
                messages.info(request, "Your email is already verified.")
                return redirect('auth:login')
        else:

            messages.error(request, "Invalid or expired confirmation link.")
            return redirect('auth:signup')

class LoginView(View):
    template_name = 'custom_auth/login.html'

    def get(self, request):

        if request.user.is_authenticated:
            return redirect('crm:customer_list')

        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                if not user.email_verified:
                    messages.error(request, 'Your account has not been verified. Please confirm your email.')
                    return render(request, self.template_name, {'form': form})

                user = authenticate(request, email=email, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('crm:customer_list')

                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'A user with this email does not exist.')

        return render(request, self.template_name, {'form': form})

class PasswordResetRequestView(View):
    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, 'custom_auth/password_reset_request.html', {'form': form})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            token = get_random_string(32)

            user.reset_password_token = token
            user.save()

            reset_link = request.build_absolute_uri(
                reverse('auth:reset_password_confirm', kwargs={'uid': user.id, 'token': token})
            )

            send_confirmation_email_celery([email], 'Activate your account', f'Here is the link to activate your account: {reset_link}')

            messages.success(request, 'Password recovery instructions have been sent to your email.')
            return redirect('auth:login')

        return render(request, 'custom_auth/password_reset_request.html', {'form': form})

class PasswordResetConfirmView(View):
    def get(self, request, uid, token):
        user = get_object_or_404(User, id=uid, reset_password_token=token)
        form = PasswordResetForm(user)
        return render(request, 'custom_auth/password_reset_confirm.html', {'form': form})

    def post(self, request, uid, token):
        user = get_object_or_404(User, id=uid, reset_password_token=token)
        form = PasswordResetForm(user, request.POST)

        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.reset_password_token = ''
            user.save()

            messages.success(request, 'Password successfully updated! You can now log in.')
            return redirect('auth:login')

        return render(request, 'custom_auth/password_reset_confirm.html', {'form': form})

class CustomLogoutView(LogoutView):

    next_page = reverse_lazy('auth:main')
