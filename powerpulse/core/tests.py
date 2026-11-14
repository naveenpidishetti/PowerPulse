from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class CoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="coreuser", password="password123")

    def test_landing_page_renders(self):
        response = self.client.get(reverse("core:landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_authenticated(self):
        self.client.login(username="coreuser", password="password123")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")

    def test_user_manual_renders(self):
        response = self.client.get(reverse("core:manual"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/manual.html")
        self.assertContains(response, "Bulk CSV Upload")


