from rest_framework import generics
from .models import News, Page, NewsCategory, Tag
from .serializers import NewsSerializer, PageSerializer, NewsCategorySerializer, TagSerializer


class NewsCategoryListAPIView(generics.ListAPIView):
    queryset = NewsCategory.objects.filter(
        parent__isnull=True).order_by('name')
    serializer_class = NewsCategorySerializer
    pagination_class = None


class TagListAPIView(generics.ListAPIView):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


class NewsListAPIView(generics.ListAPIView):
    queryset = News.objects.all().order_by('-published_at')
    serializer_class = NewsSerializer


class NewsDetailAPIView(generics.RetrieveAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    lookup_field = 'slug'


class PageListAPIView(generics.ListAPIView):
    queryset = Page.objects.filter(is_published=True).order_by('-created_at')
    serializer_class = PageSerializer


class PageDetailAPIView(generics.RetrieveAPIView):
    queryset = Page.objects.filter(is_published=True)
    serializer_class = PageSerializer
    lookup_field = 'slug'
