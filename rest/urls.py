# rest/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CarouselContentListView, PageViewSet, TagViewSet, ContentViewSet,
    ContentImageViewSet, ContentTextViewSet, PageNavigationViewSet, VideoViewSet
)

router = DefaultRouter()
router.register(r'pages', PageViewSet)
router.register(r'tags', TagViewSet)
router.register(r'contents', ContentViewSet)
router.register(r'content-images', ContentImageViewSet)
router.register(r'content-texts', ContentTextViewSet)
router.register(r'videos', VideoViewSet)
router.register(r'page-navigation', PageNavigationViewSet,
                basename='page-navigation')

urlpatterns = [
    path('', include(router.urls)),
    path('carousel/', CarouselContentListView.as_view(),
         name='carousel-contents'),
]
