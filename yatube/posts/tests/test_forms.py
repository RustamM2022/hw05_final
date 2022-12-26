from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Post, Group, Follow, Comment

User = get_user_model()

POST_TEXT = 'Текст из формы'
POST_TEXT_EDIT = 'Текст изменен'
POST_COMMENT = 'Новый комментарий'


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Любой пользователь')
        cls.user_follower = User.objects.create(
            username='подписчик')
        cls.user_following = User.objects.create(
            username='избранный автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

        cls.comments = Comment.objects.create(
            text='Какой-то комментарий',
            author=cls.user,
            post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text=POST_TEXT
            ).exists()
        )

    def test_post_edit(self):
        """Убедимся, что запись в базе данных изменилась:"""
        form_data = {
            'text': POST_TEXT_EDIT,
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text=POST_TEXT_EDIT
            ).exists()
        )

    def test_authorized_user_comment_create(self):
        """Комментарии создаются авторизованным пользователем"""
        form_data = {
            'text': POST_COMMENT
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostCreateFormTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text=POST_COMMENT
            ).exists()
        )

    def test_guest_user_comment_create(self):
        """Создание комментариев недоступно неавторизованным пользователям"""
        form_data = {
            'text': 'Комментарий не создан'
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostCreateFormTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Комментарий не создан'
            ).exists()
        )

    def test_user_follower(self):
        """Убедимся, что авторизованный пользователь
        может подписываться на других авторов."""
        self.authorized_client.force_login(self.user_follower)
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user_following}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )

    def test_user_following(self):
        """Убедимся, что авторизованный пользователь
        может удалять подписки на других авторов."""
        self.authorized_client.force_login(self.user_follower)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user_following}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )

    def test_new_post_appears(self):
        """Убедимся, что новая запись пользователя
        появляется в ленте тех, кто на него подписан."""
        self.authorized_client.force_login(self.user_following)
        form_data = {
            'text': POST_TEXT
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.authorized_client.force_login(self.user_follower)
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user_following}))
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        posts_follower = response.context['page_obj'][0].text
        self.assertIn(POST_TEXT, posts_follower)

        """Убедимся, что новая запись пользователя не
        появляется в ленте тех, кто на него не подписан."""
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        posts = response.context.get('page_obj').object_list
        self.assertNotIn(POST_TEXT, posts)
