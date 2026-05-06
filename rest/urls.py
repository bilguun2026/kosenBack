# rest/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CarouselContentListView, ImportantURLViewSet, PageViewSet, TagViewSet, ContentViewSet,
    ContentImageViewSet, ContentTextViewSet, PageNavigationViewSet, VideoViewSet,
    ImportDocumentView,
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
router.register(r"urls", ImportantURLViewSet,
                basename="important-url")
urlpatterns = [
    path('', include(router.urls)),
    path('carousel/', CarouselContentListView.as_view(), name='carousel-contents'),
    path('import-document/', ImportDocumentView.as_view(), name='import-document'),
]
