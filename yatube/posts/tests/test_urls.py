from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()

HOME_URL = '/'
CREATE_TEMPLATE = 'posts/create_post.html'


class StaticURLTests(TestCase):
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Любой пользователь')
        cls.first_user = User.objects.create_user(username='first_user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.first_user
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='описание'
        )

    def setUp(self):
        self.authorized_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        для любого пользователя."""
        templates_url_names = {
            HOME_URL: 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.first_user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.pk}/': 'posts/post_detail.html',
            '/unexesting_page/': 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_create_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        для авторизованного пользователя."""
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, CREATE_TEMPLATE)

    def test_urls_create_edit_correct_template(self):
        """URL-адрес использует соответствующий шаблон для автора."""
        self.authorized_client.force_login(self.first_user)
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertTemplateUsed(response, CREATE_TEMPLATE)

    def test_urls_uses_correct_adress(self):
        """URL-адреса используют правильные адреса для любого пользователя."""
        adress_url_names = [
            HOME_URL,
            '/group/test-slug/',
            f'/profile/{self.first_user}/',
            f'/posts/{PostURLTests.post.pk}/'
        ]
        for address in adress_url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_adress_create(self):
        """URL-адреса используют правильные адреса
        для авторизованного пользователя."""
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_adress_create_edit(self):
        """URL-адреса используют правильные адреса для автора."""
        self.authorized_client.force_login(self.first_user)
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexesting_page_correct_adress(self):
        """URL-адрес использует неправильный адрес."""
        response = self.client.get('/unexesting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
