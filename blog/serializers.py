from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Category, Tag, Post, PostView, Comment

class CategorySerializer(serializers.Serializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'post_count', 'created_at']

    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()
    
class TagSerializer(serializers.Serializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'post_count'
        ]

    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()
    
class PostListSerializer(serializers.Serializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'excerpt', 'author', 'category', 'tags',
            'status', 'post_type', 'featured_image', 'is_featured', 
            'view_count', 'read_time', 'created_at', 'updated_at', 'comment_count'
        ]

    def get_comment_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
class PostDetailSerializer(PostListSerializer):
    content = serializers.CharField()
    meta_title = serializers.CharField()
    meta_description = serializers.CharField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + [
            'content', 'meta_title', 'meta_description', 'published_at'
        ]

class CommentSerializer(serializers.Serializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent', 'content', 'is_approved',
            'created_at', 'updated_at', 'replies', 'can_edit'
        ]
        read_only_fields = ['author', 'post']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.filter(is_approved=True), many=True).data
        return []

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False
    
class PostViewSerializer(serializers.Serializer):
    class Meta:
        model = PostView
        fields = [
            'id', 'post', 'user', 'ip_address', 'timestamp'
        ]

class BlogStatsSerializer(serializers.Serializer):
    total_posts = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_comments  = serializers.IntegerField()
    popular_posts = PostListSerializer(many=True)
    recent_posts = PostListSerializer(many=True)