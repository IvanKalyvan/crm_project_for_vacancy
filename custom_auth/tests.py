import uuid

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import PasswordResetRequestForm

class MainPageTests(TestCase):

    def test_main_page(self):

        url = reverse('auth:main')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'custom_auth/main.html')

        self.assertIn('main', response.context)
        self.assertEqual(response.context['main'], 'Welcome to the Main Page!')

class SignUpViewTest(TestCase):

    def setUp(self):
        self.signup_url = reverse('auth:signup')
        self.user_model = get_user_model()
        self.factory = RequestFactory()

    def test_user_creation_with_valid_data(self):

        data = {
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }

        response = self.client.post(self.signup_url, data)

        self.assertTrue(self.user_model.objects.filter(email=data['email']).exists())

        user = self.user_model.objects.get(email=data['email'])

        self.assertFalse(user.email_verified)

        self.assertIsNotNone(user.confirmation_token)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your account', mail.outbox[0].subject)

        self.assertTemplateUsed(response, 'custom_auth/email_verification_prompt.html')

    def test_user_creation_with_existing_email(self):

        self.user_model.objects.create(
            email='existing@example.com',
            password='existingpassword',
            email_verified=False,
            confirmation_token=None,
            created_at=timezone.now(),
            uid=uuid.uuid4()
        )

        data = {
            'email': 'existing@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }

        response = self.client.post(self.signup_url, data, follow=True)

        self.assertEqual(self.user_model.objects.filter(email='existing@example.com').count(), 1)

        self.assertContains(response, 'User with this Email already exists.')

    def test_user_creation_with_invalid_email(self):

        data = {
            'email': 'not-an-email',
            'password': 'normalpassword',
            'confirm_password': 'normalpassword'
        }

        response = self.client.post(self.signup_url, data, follow=True)

        self.assertFalse(self.user_model.objects.filter(email='not-an-email').exists())

        self.assertContains(response, 'Enter a valid email address.')

    def test_user_creation_with_short_password(self):

        data = {
            'email': 'existing@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }

        response = self.client.post(self.signup_url, data, follow=True)

        self.assertFalse(self.user_model.objects.filter(email='existing@example.com').exists())

        self.assertContains(response, 'Password is too short')

    def test_user_creation_with_long_password(self):

        data = {
            'email': 'existing@example.com',
            'password': 'longlonglonglonglonglonglonglonglonglonglong',
            'confirm_password': 'longlonglonglonglonglonglonglonglonglonglong'
        }

        response = self.client.post(self.signup_url, data, follow=True)

        self.assertFalse(self.user_model.objects.filter(email='existing@example.com').exists())

        self.assertContains(response, 'Password is too long')

    def test_user_creation_with_password_mismatch(self):

        data = {
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'wrongpassword'
        }

        response = self.client.post(self.signup_url, data, follow=True)

        self.assertFalse(self.user_model.objects.filter(email='testuser@example.com').exists())

        self.assertContains(response, 'Passwords do not match')

class ConfirmEmailViewTest(TestCase):
    def setUp(self):

        self.signup_url = reverse('auth:signup')
        self.user_model = get_user_model()

        self.user = self.user_model.objects.create(
            email='setup@example.com',
            password='securepassword123',
            email_verified=False,
            confirmation_token='valid-token',
            uid=uuid.uuid4(),
        )

        self.confirm_email_url = reverse(
            'auth:confirm_email',
            kwargs={'uid': self.user.uid, 'token': self.user.confirmation_token}
        )

    def test_valid_confirmation_token(self):

        user = self.user_model.objects.create(
            email='testuser@example.com',
            password='securepassword123',
            email_verified=False,
            confirmation_token='valid-token',
            uid=uuid.uuid4(),
        )

        url = reverse('auth:confirm_email', kwargs={'uid': user.uid, 'token': 'valid-token'})

        response = self.client.get(url)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertIsNone(user.confirmation_token)

        self.assertTemplateUsed(response, 'custom_auth/email_verified.html')
        self.assertContains(response, "Your email has been successfully confirmed.")

    def test_invalid_confirmation_token(self):

        user = self.user_model.objects.create(
            email='testuser@example.com',
            password='securepassword123',
            email_verified=False,
            confirmation_token='valid-token',
            uid=uuid.uuid4(),
        )

        url = reverse('auth:confirm_email', kwargs={'uid': user.uid, 'token': 'invalid-token'})

        response = self.client.get(url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Invalid or expired confirmation link.', messages)

        user.refresh_from_db()
        self.assertFalse(user.email_verified)
        self.assertEqual(user.confirmation_token, 'valid-token')

        self.assertRedirects(response, self.signup_url)

    def test_email_already_verified(self):

        user = self.user_model.objects.create(
            email='testuser@example.com',
            password='securepassword123',
            email_verified=True,
            confirmation_token=None,
            uid=uuid.uuid4(),
        )

        url = reverse('auth:confirm_email', kwargs={'uid': user.uid, 'token': self.user.confirmation_token})

        response = self.client.get(url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Invalid or expired confirmation link.', messages)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)

        self.assertRedirects(response, reverse('auth:signup'))

class LoginViewTest(TestCase):
    def setUp(self):

        self.user_model = get_user_model()
        self.user = self.user_model.objects.create(
            email='test@example.com',
            email_verified=True,
            confirmation_token=None,
            created_at=timezone.now(),
            uid=uuid.uuid4()
        )
        self.user.set_password('TestPassword123')
        self.user.save()
        self.login_url = reverse('auth:login')

    def test_login_success(self):

        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'TestPassword123'})

        self.assertRedirects(response, reverse('crm:customer_list'))

    def test_login_unverified_email(self):

        self.user.email_verified = False
        self.user.save()

        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'TestPassword123'})
        self.assertContains(response, 'Your account has not been verified. Please confirm your email.')

    def test_login_invalid_credentials(self):

        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'WrongPassword'})
        self.assertContains(response, 'Invalid email or password.')

    def test_login_nonexistent_user(self):

        response = self.client.post(self.login_url, {'email': 'nonexistent@example.com', 'password': 'SomePassword'})
        self.assertContains(response, 'A user with this email does not exist.')

    def test_authenticated_user_redirect(self):

        self.client.login(email='test@example.com', password='TestPassword123')
        response = self.client.get(self.login_url)

        self.assertRedirects(response, reverse('crm:customer_list'))

class PasswordResetRequestViewTest(TestCase):
    def setUp(self):

        self.user_model = get_user_model()
        self.user = self.user_model.objects.create(
            email='test@example.com',
            email_verified=True,
            confirmation_token=None,
            created_at=timezone.now(),
            uid=uuid.uuid4()
        )
        self.password_reset_url = reverse('auth:password_reset')

    def test_get_request(self):

        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'custom_auth/password_reset_request.html')
        self.assertIsInstance(response.context['form'], PasswordResetRequestForm)

    def test_post_valid_email(self):

        response = self.client.post(self.password_reset_url, {'email': 'test@example.com'})

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.reset_password_token)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your account', mail.outbox[0].subject)
        self.assertIn(self.user.reset_password_token, mail.outbox[0].body)

        self.assertRedirects(response, reverse('auth:login'))

    def test_post_invalid_email(self):

        response = self.client.post(self.password_reset_url, {'email': 'fake@example.com'})

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(response.status_code, 200)

class PasswordResetTests(TestCase):

    def setUp(self):

        self.user_model = get_user_model()
        self.user = self.user_model.objects.create(
            email="test@example.com",
            password="OldPassword123",
            email_verified=True,
            confirmation_token=None,
            created_at=timezone.now(),
            uid=uuid.uuid4()
        )
        self.reset_request_url = reverse('auth:password_reset')

    def test_password_reset_confirm_success(self):

        token = get_random_string(32)
        self.user.reset_password_token = token
        self.user.save()

        reset_url = reverse('auth:reset_password_confirm', kwargs={'uid': self.user.id, 'token': token})
        response = self.client.post(reset_url, {'new_password1': 'NewPassword123!', 'new_password2': 'NewPassword123!'})

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        self.assertEqual(self.user.reset_password_token, '')
        self.assertRedirects(response, reverse('auth:login'))

class CustomLogoutViewTest(TestCase):

    def setUp(self):

        self.user_model = get_user_model()
        self.user = self.user_model.objects.create(
            email = 'testuser@example.com',
            email_verified = True,
            confirmation_token = None,
            created_at = timezone.now(),
            uid = uuid.uuid4()
        )
        self.user.set_password("TestPassword123")
        self.logout_url = reverse('auth:logout')
        self.main_url = reverse('auth:login')

    def test_logout_redirect(self):

        self.client.login(email="testuser@example.com", password="TestPassword123")

        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.main_url)

        response = self.client.get(self.main_url)
        self.assertContains(response, 'Registration', status_code=200)