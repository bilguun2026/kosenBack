from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Page, Tag, Content, ContentImage, ContentText
from django.forms import Textarea

# Inline for Content within Page


class ContentInline(admin.TabularInline):
    model = Content
    extra = 1
    fields = ['title', 'slug', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['tags']
    show_change_link = True
    autocomplete_fields = ['tags']  # Requires django-admin-autocomplete

# Inline for ContentImage within Content


class ContentImageInline(admin.TabularInline):
    model = ContentImage
    extra = 1
    fields = ['image', 'image_preview', 'text', 'order']
    readonly_fields = ['image_preview']
    ordering = ['order']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image Preview'

# Inline for ContentText within Content


class ContentTextInline(admin.TabularInline):
    model = ContentText
    extra = 1
    fields = ['text', 'order']
    ordering = ['order']
    formfield_overrides = {
        ContentText.text: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'parent',
                    'template', 'is_published', 'created_at']
    list_filter = ['template', 'is_published', 'parent']
    search_fields = ['title', 'subtitle']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['parent']
    autocomplete_fields = ['parent']  # Requires django-admin-autocomplete
    inlines = [ContentInline]
    list_editable = ['is_published']
    list_per_page = 25
    actions = ['publish_pages', 'unpublish_pages']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('children', 'contents')

    def publish_pages(self, request, queryset):
        queryset.update(is_published=True)
    publish_pages.short_description = "Publish selected pages"

    def unpublish_pages(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_pages.short_description = "Unpublish selected pages"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'page_link', 'tags_list']
    list_filter = ['page', 'tags']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['page']
    autocomplete_fields = ['tags']
    inlines = [ContentImageInline, ContentTextInline]
    list_per_page = 25

    def page_link(self, obj):
        if obj.page:
            url = reverse('admin:rest_page_change', args=[obj.page.id])
            return format_html('<a href="{}">{}</a>', url, obj.page.title)
        return "-"
    page_link.short_description = 'Page'

    def tags_list(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
    tags_list.short_description = 'Tags'

    class Media:
        css = {
            'all': ('admin/css/dragdrop.css',)
        }
        js = (
            'admin/js/jquery.min.js',
            'admin/js/jquery-ui.min.js',
            'admin/js/dragdrop.js',
        )


@admin.register(ContentImage)
class ContentImageAdmin(admin.ModelAdmin):
    list_display = ['content', 'image_preview', 'text', 'order']
    list_filter = ['content']
    search_fields = ['text']
    raw_id_fields = ['content']
    list_per_page = 25

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image'


@admin.register(ContentText)
class ContentTextAdmin(admin.ModelAdmin):
    list_display = ['content', 'text_preview', 'order']
    list_filter = ['content']
    search_fields = ['text']
    raw_id_fields = ['content']
    list_per_page = 25

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'
