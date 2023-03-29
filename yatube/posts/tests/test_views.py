import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        cls.second_group = Group.objects.create(
            title="группа2", slug="group_test2", description="группа тестов2")
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.author_user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.author_user)

    def test_pages_uses_correct_template_for_authorized_user(self):
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

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_nonauthorized_user(self):
        guest_client = Client()

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'group_test'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'author'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        response = self.author_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['page_obj'][0].image.name,
                         f'posts/{self.uploaded}')

    def test_group_list_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_test'}))
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.group, response.context['group'])
        self.assertEqual(response.context['page_obj'][0].image.name,
                         f'posts/{self.uploaded}')

    def test_profile_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author'}))
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.author_user, response.context['author'])
        self.assertEqual(response.context['page_obj'][0].image.name,
                         f'posts/{self.uploaded}')

    def test_post_detail_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertIn('post', response.context)
        self.assertEqual(self.post, response.context['post'])
        self.assertEqual(response.context['post'].image.name,
                         f'posts/{self.uploaded}')

    def test_post_edit_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertIn('is_edit', response.context)

    def test_post_create_show_correct_context(self):
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
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

    def test_cache(self):
        post = Post.objects.create(text=self.post.text,
                                   author=self.author_user, group=self.group)

        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(post, response.context['page_obj'][0])

        post.delete()
        response_after_del = self.author_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_after_del.content)

        cache.clear()
        response_after_clear = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_after_clear.content)


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


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author_user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author_user)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_for_authorized_user(self):
        """Авторизованный пользователь может подписываться"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'author'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_for_authorized_user(self):
        """Авторизованный пользователь может удалять из подписок"""
        Follow.objects.create(user=self.user, author=self.author_user)
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username': 'author'}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_for_follower(self):
        """Новая запись пользователя появляется в ленте"""
        new_post = Post.objects.create(text=self.post.text,
                                       author=self.author_user)
        Follow.objects.create(user=self.user, author=self.author_user)
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_new_post_for_not_follower(self):
        """Новая запись пользователя не появляется в ленте у неподписчиков"""
        Post.objects.create(text=self.post.text, author=self.author_user)
        follow = Follow.objects.create(user=self.user, author=self.author_user)
        follow.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertEqual(len(response.context['page_obj']), 0)
