from django import forms
from django.core.validators import RegexValidator

from .models import Customer

class CustomerForm(forms.ModelForm):

    phone = forms.CharField(
        validators=[RegexValidator(regex=r'^\d+$', message="Enter a valid phone number.")],
        required=True
    )

    email = forms.CharField(
        validators=[RegexValidator(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            message="Enter a valid email address.")],
        required=True
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone']
