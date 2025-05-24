from django.urls import path
from .views import (
    NewsListAPIView, NewsDetailAPIView,
    PageListAPIView, PageDetailAPIView,
    NewsCategoryListAPIView,
    TagListAPIView
)

urlpatterns = [
    path('api/news-categories/', NewsCategoryListAPIView.as_view(),
         name='news-category-list'),
    path('api/tags/', TagListAPIView.as_view(), name='tag-list'),
    path('api/news/', NewsListAPIView.as_view(), name='news-list'),
    path('api/news/<slug:slug>/', NewsDetailAPIView.as_view(), name='news-detail'),
    path('api/pages/', PageListAPIView.as_view(), name='page-list'),
    path('api/pages/<slug:slug>/', PageDetailAPIView.as_view(), name='page-detail'),
]
