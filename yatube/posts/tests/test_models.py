from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


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
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        help_text = self.post.text[:15]
        self.assertEqual(help_text, str(post))

        group = PostModelTest.group
        self.assertEqual(group.title, str(group))

    def test_models_have_correct_verbose(self):
        post = PostModelTest.post
        verbose = post._meta.get_field('author').verbose_name
        self.assertEqual(verbose, 'автор поста')

    def test_models_have_correct_help_text(self):
        post = PostModelTest.post
        expected = post._meta.get_field('group').help_text
        self.assertEqual(expected, 'Группа, к которой будет относиться пост')
