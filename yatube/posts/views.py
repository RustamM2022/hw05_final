from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .utils import get_page_context
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post, User, Comment

POSTS_PER_PAGE = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    context = get_page_context(Post.objects.all(), request)
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_count = Post.objects.all().filter(author=author).count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        "author": author,
        "posts_count": posts_count,
        'following': following
    }
    context.update(get_page_context(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    author_post = post.author.posts.count()
    comments = Comment.objects.filter(post=post)
    context = {
        "post": post,
        "author_post": author_post,
        "comments": comments,
        "form": form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    follows = user.follower.all()
    authors = [follow.author for follow in follows]
    posts = Post.objects.filter(author__in=authors)
    context = get_page_context(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_count = Follow.objects.all().filter(
        user=request.user, author=author).count()
    if request.user != author and follow_count < 1:
        Follow.objects.create(user=request.user, author=author)
        return redirect('posts:profile', username=username)
    return render(request, 'core/403.html', status=403)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
