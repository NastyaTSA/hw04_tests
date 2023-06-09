from django.test import TestCase

from ..models import Group, Post, User

TEXT_LEN: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост111111111111111111111111111111111111111111',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(PostModelTest.post.text[:TEXT_LEN],
                         str(PostModelTest.post))

    def test_group_have_correct_title(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(PostModelTest.group.title, str(PostModelTest.group))
