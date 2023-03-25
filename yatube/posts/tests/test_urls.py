# posts/tests/test_urls.py
from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        cls.post = Post.objects.create(
            text="Тестовый текст", author=cls.author_user, group=cls.group)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Cоздаем клиент автора
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author_user)

    def test_post_urls_guest(self):
        urls_guest = {
            "/": 200,
            "/group/group_test/": 200,
            "/profile/author/": 200,
            "/posts/1/": 200,
            "/posts/1/edit/": 302,
            "/create/": 302,
            "/unexisting_page/": 404}

        for address, status in urls_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_urls_authorized(self):
        urls_authorized = {
            "/": 200,
            "/group/group_test/": 200,
            "/profile/author/": 200,
            "/posts/1/": 200,
            "/posts/1/edit/": 302,
            "/create/": 200,
            "/unexisting_page/": 404}

        for address, status in urls_authorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_urls_author(self):
        urls_author = {
            "/": 200,
            "/group/group_test/": 200,
            "/profile/author/": 200,
            "/posts/1/": 200,
            "/posts/1/edit/": 200,
            "/create/": 200,
            "/unexisting_page/": 404}

        for address, status in urls_author.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_used_templates(self):
        urls_templates = {
            "/": "posts/index.html",
            "/group/group_test/": "posts/group_list.html",
            "/profile/author/": "posts/profile.html",
            "/posts/1/": "posts/post_detail.html",
            "/posts/1/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html"}

        for address, template in urls_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
