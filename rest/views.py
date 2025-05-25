# rest/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Page, Tag, Content, ContentImage, ContentText
from .serializers import (
    PageSerializer, TagSerializer, ContentSerializer,
    ContentImageSerializer, ContentTextSerializer, PageNavigationSerializer
)


class ReadOnlyOrAdminPermission(IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user and request.user.is_staff


class PageNavigationViewSet(viewsets.ReadOnlyModelViewSet):
    # Only top-level published pages
    queryset = Page.objects.filter(is_published=True, parent__isnull=True)
    serializer_class = PageNavigationSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template']
    search_fields = ['title']
    ordering_fields = ['title']
    ordering = ['title']

    def get_queryset(self):
        return Page.objects.filter(is_published=True, parent__isnull=True).prefetch_related('children')


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'is_published', 'parent']
    search_fields = ['title', 'subtitle']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']

    def get_queryset(self):
        return Page.objects.prefetch_related('contents__tags', 'contents__images', 'contents__texts', 'children')


# Rest of the viewsets (unchanged)
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['page', 'tags']
    search_fields = ['title']
    ordering_fields = ['title', 'page']
    ordering = ['title']

    def get_queryset(self):
        return Content.objects.select_related('page').prefetch_related('tags', 'images', 'texts')


class ContentImageViewSet(viewsets.ModelViewSet):
    queryset = ContentImage.objects.all()
    serializer_class = ContentImageSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['content']
    search_fields = ['text']
    ordering_fields = ['order', 'content']
    ordering = ['order']


class ContentTextViewSet(viewsets.ModelViewSet):
    queryset = ContentText.objects.all()
    serializer_class = ContentTextSerializer
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['content']
    search_fields = ['text']
    ordering_fields = ['order', 'content']
    ordering = ['order']
