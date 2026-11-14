from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpassword123", email="test@example.com")

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_success(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "testuser",
            "password": "testpassword123",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

    def test_demo_login(self):
        response = self.client.get(reverse("accounts:demo_login"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.context["user"].username, "admin")

    def test_register_page_renders(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("accounts:logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

