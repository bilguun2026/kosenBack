# rest/views.py
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Page, Tag, Content, ContentImage, ContentText, VideoUrl
from .serializers import (
    ContentListSerializer, PageSerializer, TagSerializer, ContentSerializer,
    ContentImageSerializer, ContentTextSerializer, PageNavigationSerializer, VideoSerializer
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
    permission_classes = [ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tags__slug']  # Allow ?tags__name=School
    search_fields = ['title']  # Disable ?search=
    ordering_fields = ['title', 'page', 'created_at']
    ordering = ['title']

    def get_queryset(self):
        queryset = Content.objects.select_related(
            'page').prefetch_related('tags', 'images', 'texts')
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ContentListSerializer
        return ContentSerializer


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


class CarouselContentListView(generics.ListAPIView):
    queryset = Content.objects.filter(isCarousel=True)
    serializer_class = ContentSerializer


class VideoViewSet(ReadOnlyModelViewSet):
    queryset = VideoUrl.objects.all()
    serializer_class = VideoSerializer
