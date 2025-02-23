from django.db import models

from custom_auth.models import User

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')  # Связь с User
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Deal(models.Model):
    title = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="deals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
