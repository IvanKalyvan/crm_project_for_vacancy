import json

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from unittest.mock import patch

from .models import Customer

class CustomerViewsTests(TestCase):

    def setUp(self):

        self.user_model = get_user_model()
        self.user = self.user_model.objects.create(
            email="testuser@example.com",
            email_verified=True
        )
        self.user.set_password("testpassword123")
        self.user.save()
        self.user2 = self.user_model.objects.create(
            email="testuser2@example.com",
            email_verified=True
        )
        self.user2.set_password("testpassword123")
        self.user2.save()
        self.anonymous_user = self.user_model.objects.create(
            email="anonuser@example.com",
            email_verified=False
        )
        self.anonymous_user.set_password("anonpassword123")
        self.anonymous_user.save()

        self.customer = Customer.objects.create(
            user=self.user,
            name="Test Customer",
            email="customer@example.com"
        )

        self.url = reverse('crm:customer_list')
        self.update_url = reverse('crm:customer_update', kwargs={'pk': self.customer.pk})
        self.delete_url = reverse('crm:customer_delete', kwargs={'pk': self.customer.pk})

    def test_customer_list_authenticated_verified_user(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/customer_list.html')

        self.assertContains(response, "Test Customer")

    def test_customer_list_authenticated_unverified_user(self):

        self.client.force_login(self.anonymous_user)

        response = self.client.get(self.url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Your email is not verified. Please verify your email.', messages)

    def test_customer_list_anonymous_user(self):

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("auth:login"))

    def test_delete_customers(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        data = json.dumps({"ids": [self.customer.id]})
        response = self.client.post(self.url, data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True, 'deleted_count': 1})

        self.assertFalse(Customer.objects.filter(id=self.customer.id).exists())

    def test_delete_customers_permission_error(self):

        self.client.login(email="testuser2@example.com", password="testpassword123")

        data = json.dumps({"ids": [self.customer.id]})
        response = self.client.post(self.url, data, content_type='application/json')

        self.assertJSONEqual(response.content, {'success': False, 'error': 'You do not have permission to delete these entries'})

    def test_delete_customers_invalid_json(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        data = "invalid json"
        response = self.client.post(self.url, data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'Invalid JSON'})

    def test_delete_customers_no_ids(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        data = json.dumps({})
        response = self.client.post(self.url, data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'IDs for deletion not specified'})

    def test_create_customer_invalid_form(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        test_cases = [

            ({}, ["Name", "Email", "Phone"]),

            ({"name": "John"}, ["Email", "Phone"]),

            ({"name": "John", "email": "john@example.com"}, ["Phone"]),

            ({"name": "John", "email": "not-an-email!@#$$%%$$##", "phone": "1234567890"}, ["Enter a valid email address."]),

            ({"name": "John", "email": "john@example.com", "phone": "abcd"}, ["Enter a valid phone number."])
        ]

        for data, expected_errors in test_cases:
            response = self.client.post(reverse("crm:customer_create"), data=data)
            self.assertEqual(response.status_code, 200)

            for error in expected_errors:
                with self.subTest(data=data, error=error):
                    self.assertContains(response, error)

    def test_update_customer_authenticated_owner(self):

        self.client.login(email="testuser@example.com", password="testpassword123")
        response = self.client.post(self.update_url, {
            'name': "Updated Customer",
            'email': "updated@example.com",
            'phone': "9876543210"
        })

        self.customer.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.customer.name, "Updated Customer")
        self.assertEqual(self.customer.email, "updated@example.com")
        self.assertEqual(self.customer.phone, "9876543210")

    def test_update_customer_authenticated_not_owner(self):

        self.client.login(email="testuser2@example.com", password="testpassword123")
        response = self.client.post(self.update_url, {
            'name': "Hacker Customer",
            'email': "hacker@example.com",
            'phone': "0000000000"
        })

        self.assertEqual(response.status_code, 404)

    def test_delete_customer_authenticated_owner(self):

        self.client.login(email="testuser@example.com", password="testpassword123")

        response = self.client.post(self.delete_url)

        self.assertRedirects(response, reverse("crm:customer_list"))
        self.assertFalse(Customer.objects.filter(id=self.customer.id).exists())

    def test_delete_customer_authenticated_not_owner(self):

        self.client.login(email="testuser2@example.com", password="testpassword123")

        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Customer.objects.filter(id=self.customer.id).exists())

    def test_delete_customer_ajax_request(self):

        self.client.login(email="testuser@example.com", password="testpassword123")
        response = self.client.delete(self.delete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertJSONEqual(response.content, {"success": True})
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    @patch("crm.views.Customer.delete")
    def test_delete_customer_failure(self, mock_delete):

        mock_delete.side_effect = Exception("Database error")

        self.client.login(email="testuser@example.com", password="testpassword123")
        response = self.client.delete(self.delete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(response.content, {"success": False, "message": "Database error"})
        self.assertTrue(Customer.objects.filter(id=self.customer.id).exists())