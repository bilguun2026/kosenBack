from rest_framework import serializers
from .models import News, NewsCategory, PageImage, Tag, Page


class NewsSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategory
        fields = ['id', 'name', 'slug']


class NewsCategorySerializer(serializers.ModelSerializer):
    category_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsCategory
        fields = ['id', 'name', 'slug', 'category_url', ]

    def get_category_url(self, obj):
        return self.context['request'].build_absolute_uri(f'/categories/news/{obj.slug}/')


class TagSerializer(serializers.ModelSerializer):
    tag_url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'tag_url']

    def get_tag_url(self, obj):
        return self.context['request'].build_absolute_uri(f'/tags/{obj.slug}/')


class NewsSerializer(serializers.ModelSerializer):
    category = NewsCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    news_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'content', 'image_url', 'news_url',
            'category', 'tags', 'published_at', 'updated_at'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def get_news_url(self, obj):
        return self.context['request'].build_absolute_uri(f'/news/{obj.slug}/')


class PageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageImage
        fields = ['id', 'image', 'text', 'order']
        read_only_fields = ['id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation


class PageSerializer(serializers.ModelSerializer):
    images = PageImageSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = [
            'id', 'title', 'subtitle', 'slug', 'body', 'template',
            'is_published', 'created_at', 'updated_at', 'images'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class PageUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'name', 'slug']
