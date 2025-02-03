from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm

from .models import User

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = User
        fields = ['email']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return confirm_password

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 10:
            raise ValidationError("Password is too short")
        if len(password) > 30:
            raise ValidationError("Password is too long")
        return password

class LoginForm(forms.Form):

    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email was not found.")
        return email

class PasswordResetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        strip=False,
    )