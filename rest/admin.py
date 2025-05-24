from django.contrib import admin
from .models import News, NewsCategory, Page, PageImage,  Tag


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'category', 'published_at', 'updated_at']
    list_filter = ['category', 'tags', 'published_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'


class PageImageInline(admin.TabularInline):
    model = PageImage
    extra = 1  # Number of empty forms to display
    fields = ['image', 'text', 'order']
    ordering = ['order']


class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'slug', 'template',
                    'is_published', 'created_at', 'updated_at']
    list_filter = ['template', 'is_published']
    search_fields = ['title', 'subtitle', 'body']
    inlines = [PageImageInline]
    readonly_fields = ['id', 'slug', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'body', 'template', 'is_published')
        }),
        ('Advanced', {
            'fields': ('id', 'slug', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


class PageImageAdmin(admin.ModelAdmin):
    list_display = ['page', 'image', 'text', 'order']
    list_filter = ['page']
    search_fields = ['text']
    readonly_fields = ['id']
    ordering = ['page', 'order']


admin.site.register(Page, PageAdmin)
admin.site.register(PageImage, PageImageAdmin)
