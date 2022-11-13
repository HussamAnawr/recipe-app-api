from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):
    """Test Models for creating ang sign up."""
    def test_create_user_with_email_successuflly(self):
        email = 'hussam@example.com'
        password = 'example123'
        user = get_user_model().objects.create_user(email=email, password=password)
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_user_email_normalized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@EXAMPLE.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email=email, password='example123')
            self.assertEqual(user.email, expected)
    
    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'example123')

    def test_create_superuser_successfully(self):
        user = get_user_model().objects.create_superuser(email='example@exampl.com', password='example123')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
