from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="группа", slug="group_test", description="группа тестов")
        cls.group2 = Group.objects.create(
            title="группа2", slug="group_test2", description="группа тестов2")

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author_user)

    def test_create_post(self):
        """при отправке валидной формы со страницы создания поста reverse('posts:create_post') создаётся новая запись в базе данных"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data)
        self.assertEqual(Post.objects.count(), posts_count + 1)

        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.author_user)

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста reverse('posts:post_edit', args=('post_id',)) происходит изменение поста с post_id в базе данных."""

        self.test_create_post()

        post = Post.objects.latest('id')

        post_id = post.pk
        new_form_data = {
            'text': post.text + ' edited',
            'group': self.group2.id
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=new_form_data)
        post = Post.objects.get(pk=post_id)

        self.assertEqual(post.text, new_form_data['text'])
        self.assertEqual(post.group.id, new_form_data['group'])
