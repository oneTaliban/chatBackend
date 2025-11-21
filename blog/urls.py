from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, TagViewSet, PostViewSet, CommentViewSet, BlogStatViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'stats', BlogStatViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]