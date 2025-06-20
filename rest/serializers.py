# rest/serializers.py
from rest_framework import serializers
from .models import Page, Tag, Content, ContentImage, ContentText, VideoUrl


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


class ContentListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d')

    class Meta:
        model = Content
        fields = ['id', 'title', 'image', 'description', 'created_at', 'tags']

    def get_image(self, obj):
        first_image = obj.images.order_by('order').first()
        if first_image:
            return ContentImageSerializer(first_image, context=self.context).data
        return None


class ContentSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    images = ContentImageSerializer(many=True, read_only=True)
    texts = ContentTextSerializer(many=True, read_only=True)
    page_title = serializers.CharField(source='page.title', read_only=True)

    class Meta:
        model = Content
        fields = ['id', 'title', 'description', 'slug', 'tags',
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


class VideoSerializer(serializers.ModelSerializer):
    video_source = serializers.ReadOnlyField()

    class Meta:
        model = VideoUrl
        fields = ['id', 'title', 'url', 'video_file', 'video_source']
