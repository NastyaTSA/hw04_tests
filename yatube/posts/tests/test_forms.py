import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        cls.group2 = Group.objects.create(
            title="группа2", slug="group_test2", description="группа тестов2")

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.author_user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author_user)

    def test_create_post_for_authorized_user(self):
        """при отправке валидной формы со страницы создания поста
        reverse('posts:create_post') создаётся новая запись в базе данных"""
        posts_count = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), posts_count + 1)

        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.author_user)
        self.assertEqual(post.image, f'posts/{uploaded}')

    def test_create_post_for_nonauthorized_user(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста без авторизации',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text=form_data['text']).exists())

    def test_post_edit_for_authorized_user(self):
        """при отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',)) происходит изменение
        поста с post_id в базе данных."""

        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        post = Post.objects.latest('id')

        post_id = post.pk
        new_uploaded = SimpleUploadedFile(
            name='small_new.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        new_form_data = {
            'text': post.text + ' edited',
            'group': self.group2.id,
            'image': new_uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=new_form_data)
        post = Post.objects.get(pk=post_id)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(post.text, new_form_data['text'])
        self.assertEqual(post.group.id, new_form_data['group'])
        self.assertEqual(post.image, f'posts/{new_uploaded}')

    def test_post_edit_for_nonauthorized_user(self):
        """при отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',)) происходит изменение
        поста с post_id в базе данных."""

        uploaded = SimpleUploadedFile(
            name='small3.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data
        )

        posts_count = Post.objects.count()

        post = Post.objects.latest('id')

        old_form_data = {
            'text': post.text,
            'group': post.group.id
        }

        post_id = post.pk
        new_form_data = {
            'text': post.text + ' edited',
            'group': self.group2.id
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=new_form_data)
        post = Post.objects.get(pk=post_id)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Post.objects.count(), posts_count)

        self.assertEqual(post.text, old_form_data['text'])
        self.assertEqual(post.group.id, old_form_data['group'])

    def test_add_comment_authorized(self):
        """Проверка создания пользователем комментария"""
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.author_user,
            'text': 'text',
        }
        self.author_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='text',
            author=self.author_user, ).exists())
