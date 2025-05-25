# rest/serializers.py
from rest_framework import serializers
from .models import Page, Tag, Content, ContentImage, ContentText


class PageNavigationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'children']

    def get_children(self, obj):
        # Recursively serialize children (subpages) that are published
        children = obj.children.filter(is_published=True)
        return PageNavigationSerializer(children, many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ContentImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ContentImage
        fields = ['id', 'image', 'image_url', 'text', 'order']

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class ContentTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentText
        fields = ['id', 'text', 'order']


class ContentSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    images = ContentImageSerializer(many=True, read_only=True)
    texts = ContentTextSerializer(many=True, read_only=True)
    page_title = serializers.CharField(source='page.title', read_only=True)

    class Meta:
        model = Content
        fields = ['id', 'title', 'slug', 'tags',
                  'page', 'page_title', 'images', 'texts']


class PageSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True, read_only=True)
    template_display = serializers.CharField(
        source='get_template_display', read_only=True)
    children = PageNavigationSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = [
            'id', 'title', 'subtitle', 'slug', 'template', 'template_display',
            'is_published', 'created_at', 'updated_at', 'contents', 'children'
        ]
