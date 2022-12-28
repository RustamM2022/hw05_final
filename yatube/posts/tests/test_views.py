import shutil
import tempfile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group


User = get_user_model()

HOME_URL = reverse('posts:index')
PROFILE_URL = reverse('posts:profile', kwargs={'username': 'first_user'})
POST_DETAIL_URL = 'posts:post_detail'
POST_EDIT_URL = 'posts:post_edit'
POST_CREATE_URL = reverse('posts:post_create')
POST_GROUP_URL = reverse('posts:group_list', kwargs={'slug': 'test-slug'})
POSTS_PER_PAGE = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMAIL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Любой пользователь')
        cls.first_user = User.objects.create_user(username='first_user')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            slug='test-slug',
            description='описание'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый текст группы 2',
            slug='test-slug2',
            description='описание группы 2'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMAIL_GIF,
            content_type='image/gif'
        )
        cls.posts = [Post.objects.create(
            text=f'Тестовый пост номер {i}',
            author=cls.first_user,
            pub_date='20.20.20 20:20',
            group=cls.group
        ) for i in range(1, 3)
        ]
        cls.post = Post.objects.create(
            text='Текст к картинке',
            author=cls.first_user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.first_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            HOME_URL: 'posts/index.html',
            PROFILE_URL: 'posts/profile.html',
            reverse(POST_DETAIL_URL, kwargs={
                'post_id': PostViewsTests.posts[0].id}): (
                    'posts/post_detail.html'),
            reverse(POST_EDIT_URL, kwargs={
                'post_id': PostViewsTests.posts[0].id}): (
                    'posts/create_post.html'),
            POST_CREATE_URL: 'posts/create_post.html',
            POST_GROUP_URL: 'posts/group_list.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Выведен правильный список постов."""
        cache.clear()
        response = self.authorized_client.get(HOME_URL)
        posts = response.context.get('page_obj').object_list

        for index in range(3, 1):
            post = (self.posts[index])
            with self.subTest(post=post):
                self.assertEqual(
                    (post.text, post.id),
                    ((posts[index].text, posts[index].id))
                )

    def test_group_context(self):
        """Выведен список постов по группам."""
        response = self.authorized_client.get(POST_GROUP_URL)
        groups = response.context['page_obj'].object_list
        for index in range(3, 1):
            post_group = (self.posts[index])
            with self.subTest(post_group=post_group):
                self.assertEqual(
                    (post_group.text, post_group.id),
                    ((groups[index].text, groups[index].id))
                )

    def test_profile_context(self):
        """Выведен список постов по пользователю."""
        response = self.authorized_client.get(PROFILE_URL)
        users_post = response.context['page_obj'].object_list[0]
        for index in range(3, 1):
            post_user = (self.posts[index])
            with self.subTest(post_user=post_user):
                self.assertEqual(
                    (post_user.text, post_user.id),
                    ((users_post[index].text, users_post[index].id))
                )

    def test_post_detail_context(self):
        """Выведен пост по id."""
        response = self.authorized_client.get(reverse(
            POST_DETAIL_URL, kwargs={
                'post_id': PostViewsTests.posts[0].id}))
        id_post = response.context.get('post')
        self.assertEqual(id_post, self.posts[0])

    def test_post_create_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Шаблон create для редактирования поста сформирован
        с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse(
            POST_EDIT_URL, kwargs={'post_id': PostViewsTests.posts[0].id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_list_ver(self):
        """Пост не попал на страницу другой группы."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug2'}))
        posts_add = response.context.get('page_obj')
        self.assertNotIn(self.posts, posts_add)

    def test_post_url_context(self):
        """Пост появляется на главной странице сайта,
        странице группы и пользователя.'"""
        response_urls = {
            'index': self.authorized_client.get(HOME_URL),
            'group_list': self.authorized_client.get(POST_GROUP_URL),
            'profile': self.authorized_client.get(PROFILE_URL)
        }
        for url, response in response_urls.items():
            with self.subTest(url=url):
                post_page = response.context.get('page_obj')
                self.assertIn(self.posts[0], post_page)

    def test_cache_index(self):
        """Проверка кеширования на главной странице сайта."""
        response = self.authorized_client.get(HOME_URL)
        posts = response.content
        Post.objects.create(
            text='Тестовый пост',
            author=self.first_user,
        )
        response_old = self.authorized_client.get(HOME_URL)
        posts_old = response_old.content
        self.assertEqual(posts, posts_old)
        cache.clear()
        response_new = self.authorized_client.get(HOME_URL)
        posts_new = response_new.content
        self.assertNotEqual(posts_new, posts_old)

    def test_create_image(self):
        """Проверка сохранения рисунка."""
        cache.clear()
        adress_url_names = [
            HOME_URL,
            POST_GROUP_URL,
            PROFILE_URL
        ]
        for address in adress_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                posts = response.context.get('page_obj')
                self.assertEqual('posts/small.gif', posts[0].image)
        response_detail = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        posts_detail = response_detail.context.get('post')
        self.assertEqual('posts/small.gif', posts_detail.image)
        self.assertTrue(
            Post.objects.filter(
                text='Текст к картинке',
                image='posts/small.gif'
            ).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Любой пользователь')
        cls.first_user = User.objects.create_user(username='first_user')
        cls.group = Group.objects.create(
            title='Тестовый титул',
            slug='test-slug',
            description='описание'
        )
        post = Post(
            text='Тестовый пост',
            author=cls.first_user,
            pub_date='10.10.10 10:10',
            group=cls.group
        )
        posts = (post for i in range(1, 14))
        Post.objects.bulk_create(posts)

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.first_user)

    def test_first_page_index(self):
        """Главная страница: количество постов на первой странице равно 10."""
        response = self.authorized_client.get(HOME_URL)
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_page__index(self):
        """Главная страница: на второй странице должно быть три поста."""
        POSTS_SECOND_PAGE = Post.objects.all().count() - POSTS_PER_PAGE
        response = self.authorized_client.get(HOME_URL + '?page=2')
        self.assertEqual(len(response.context['page_obj']), POSTS_SECOND_PAGE)

    def test_first_page_group_list(self):
        """Страницы группы: количество постов на первой странице равно 10."""
        response = self.authorized_client.get(POST_GROUP_URL)
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_first_page_profile(self):
        """Страница пользователя: количество постов
         на первой странице равно 10."""
        response = self.authorized_client.get(PROFILE_URL)
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)
