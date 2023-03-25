from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import User, Group, Post


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        cls.second_group = Group.objects.create(
            title="группа2", slug="group_test2", description="группа тестов2")
        cls.post = Post.objects.create(
            text="Тестовый текст", author=cls.author_user, group=cls.group)

    def setUp(self):
        # Cоздаем клиент автора
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.author_user)

    def test_pages_uses_correct_template(self):
        """Задание 1: проверка namespace:name"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'group_test'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'author'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        # Проверяем, что при обращении к name вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        response = self.author_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)

    def test_group_list_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_test'}))
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.group, response.context['group'])

    def test_profile_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author'}))
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.author_user, response.context['author'])

    def test_post_detail_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertIn('post', response.context)
        self.assertEqual(self.post, response.context['post'])

    def test_post_edit_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        # Проверяем, что типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

        self.assertIn('is_edit', response.context)

    def test_post_create_show_correct_context(self):
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        # Проверяем, что типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_creation(self):
        """Задание 3: дополнительная проверка при создании поста"""
        response = self.author_client.get(reverse('posts:index'))
        self.assertIn(self.post, response.context['page_obj'])

        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_test'}))
        self.assertIn(self.post, response.context['page_obj'])

        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author'}))
        self.assertIn(self.post, response.context['page_obj'])

        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_test2'}))
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    """Задание 2: проверка контекста. Тестируем паджинатор"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        for post in range(13):
            cls.post = Post.objects.create(
                text='текст текст', author=cls.author_user, group=cls.group
            )

    def setUp(self):
        # Cоздаем клиент автора
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.author_user)

    def test_paginator(self):
        urls_to_test = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'group_test'}),
            reverse('posts:profile', kwargs={'username': 'author'})
        ]

        for urls in urls_to_test:
            with self.subTest(urls=urls):
                response = self.author_client.get(urls)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.author_client.get(urls + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
