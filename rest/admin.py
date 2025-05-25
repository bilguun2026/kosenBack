from django.contrib import admin
from .models import Page, Tag, Content, ContentImage, ContentText


# Inline for Content to be edited within Page
class ContentInline(admin.TabularInline):
    model = Content
    extra = 1  # Number of empty forms to display
    fields = ['title', 'slug', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    # Use raw_id_fields for ManyToMany to improve performance
    raw_id_fields = ['tags']
    show_change_link = True  # Allow clicking to edit Content details


# Inline for ContentImage to be edited within Content
class ContentImageInline(admin.TabularInline):
    model = ContentImage
    extra = 1
    fields = ['image', 'text', 'order']
    ordering = ['order']


# Inline for ContentText to be edited within Content
class ContentTextInline(admin.TabularInline):
    model = ContentText
    extra = 1
    fields = ['text', 'order']
    ordering = ['order']


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'parent',
                    'template', 'is_published', 'created_at']
    list_filter = ['template', 'is_published', 'parent']
    search_fields = ['title', 'subtitle']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['parent']  # Improves performance for large datasets
    inlines = [ContentInline]
    # Allow toggling is_published directly in list view
    list_editable = ['is_published']
    list_per_page = 25

    def get_queryset(self, request):
        # Optimize queries by prefetching related data
        return super().get_queryset(request).prefetch_related('children', 'contents')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'page', 'tags_list']
    list_filter = ['page', 'tags']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['page', 'tags']
    inlines = [ContentImageInline, ContentTextInline]
    list_per_page = 25

    def tags_list(self, obj):
        # Display tags as a comma-separated list in the admin
        return ", ".join(tag.name for tag in obj.tags.all())
    tags_list.short_description = 'Tags'


@admin.register(ContentImage)
class ContentImageAdmin(admin.ModelAdmin):
    list_display = ['content', 'image', 'text', 'order']
    list_filter = ['content']
    search_fields = ['text']
    raw_id_fields = ['content']
    list_per_page = 25


@admin.register(ContentText)
class ContentTextAdmin(admin.ModelAdmin):
    list_display = ['content', 'text_preview', 'order']
    list_filter = ['content']
    search_fields = ['text']
    raw_id_fields = ['content']
    list_per_page = 25

    def text_preview(self, obj):
        # Show a truncated version of the text for readability
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'
