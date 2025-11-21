from django.shortcuts import render
from django.db.models import Q, Count
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Category, Tag, Post, Comment, PostView
from .serializers import (
    CategorySerializer, TagSerializer, PostListSerializer, 
    PostDetailSerializer, CommentSerializer, PostView, 
    BlogStatsSerializer
)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    lookup_field = 'slug'
    serializer_class = TagSerializer

class  PostViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'category').prefetch_related('tags')

        if self.action  == 'list':
            # Only show published posts to non-authenticated users
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(status='published')
            elif not self.request.user.is_staff:
                #show users own drafts + published posts
                queryset = queryset.filter(
                    Q(status='published') |
                    Q(author=self.request.user, status='draft')
                )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        #track view
        if instance.status == 'published':
            PostView.objects.create(
                post=instance,
                user=request.user if request.user.is_authenticated else None,
                ip_address = self.get_client_ip(request),
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            )
            instance.view_count += 1
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def featured(self, reqeust):
        featured_posts = self.get_queryset().filter(
            is_featured=True,
            status='published'
        )[:5]
        serializer = self.get_serializer(featured_posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request, slug=None):
        category = Category.objects.get(slug=slug)
        posts = self.get_queryset().filter(category=category, status='published')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, slug=None):
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            return Response(
                { 'error': 'You can only publish your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        post.status = 'published'
        post.published_at = timezone.now()
        post.save()

        return Response({ 'status': 'published'})

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]
    serializer_class= CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(
            is_approved=True,
            parent__isnull=True
        ).select_related('author').prefetch_related('replies')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_post(self, request):
        post_slug = request.query_params.get('post')
        comments = self.get_queryset().filter(post__slug=post_slug)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)
    
class BlogStatViewSet(viewsets.ViewSet):
    def list(self, request):
        total_posts = Post.objects.filter(status='published')
        total_views = PostView.objects.count()
        total_comments = Comment.objects.filter(is_approved=True).count()  
        
        popular_posts = Post.objects.filter(
            status='published',
        ).order_by('-created_at')[:5]

        recent_posts = Post.objects.filter(
            status='published'
        ).order_by('-created_at')[:5]

        data = {
            'total_posts': total_posts,
            'total_views': total_views,
            'total_comments': total_comments,
            'popular_posts': PostListSerializer(popular_posts, many=True).data,
            'recent_posts': PostListSerializer(recent_posts, many=True).data
        }

        serializer = BlogStatsSerializer(data)
        return Response(serializer.data)