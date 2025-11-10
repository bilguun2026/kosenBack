from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    Page,
    Tag,
    Content,
    PageContent,
    NewsContent,
    ContentImage,
    ContentText,
    VideoUrl,
)


# ---------- INLINES ----------


class ContentInline(admin.TabularInline):
    """
    Inline for Content inside Page.
    """
    model = Content
    extra = 1
    fields = ("title", "slug", "isPage", "isCarousel", "tags")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["tags"]
    show_change_link = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("tags")


class ContentTextInline(admin.TabularInline):
    """
    Inline for text blocks inside a Content.
    CKEditor5 widget is used automatically from the model field.
    """
    model = ContentText
    extra = 1
    fields = ("text", "order")
    ordering = ("order",)


class ContentImageInline(admin.StackedInline):
    """
    Single banner image for each Content.
    """
    model = ContentImage
    extra = 1
    max_num = 1
    can_delete = True
    fields = ("image", "image_preview", "text", "order")
    readonly_fields = ("image_preview",)

    verbose_name = "Баннер"
    verbose_name_plural = "Баннер"

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 150px; '
                'border-radius:8px; object-fit:cover;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Баннерын урьдчилсан харагдац"


# ---------- PAGE ADMIN ----------


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "parent", "template", "is_published", "created_at")
    list_display_links = ("title",)
    list_filter = ("template", "is_published", "parent")
    search_fields = ("title", "subtitle")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["parent"]
    inlines = [ContentInline]
    list_editable = ("is_published",)
    list_per_page = 25
    ordering = ("-created_at",)
    actions = ["publish_pages", "unpublish_pages"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("parent").prefetch_related("children", "contents")

    def publish_pages(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} хуудас нийтлэгдлээ.")

    publish_pages.short_description = "Сонгосон хуудсуудыг нийтлэх"

    def unpublish_pages(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} хуудас нууж хадгаллаа.")

    unpublish_pages.short_description = "Сонгосон хуудсуудыг нуух"


# ---------- TAG ADMIN ----------


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
    ordering = ("name",)


# ---------- BASE CONTENT ADMIN (shared config) ----------


class BaseContentAdmin(admin.ModelAdmin):
    """
    Shared behavior for PageContentAdmin and NewsContentAdmin.
    """

    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")
    inlines = [ContentTextInline, ContentImageInline]
    list_per_page = 25
    ordering = ("title",)

    def page_link(self, obj):
        if obj.page_id:
            app_label = Page._meta.app_label
            model_name = Page._meta.model_name
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.page_id])
            return format_html('<a href="{}">{}</a>', url, obj.page.title)
        return "—"

    page_link.short_description = "Хуудас"
    page_link.admin_order_field = "page"

    def tags_list(self, obj):
        names = [t.name for t in obj.tags.all()]
        return ", ".join(names) if names else "—"

    tags_list.short_description = "Тагууд"


# ---------- PAGE CONTENT ADMIN (only isPage=True) ----------


@admin.register(PageContent)
class PageContentAdmin(BaseContentAdmin):
    """
    For content used on pages:
      - Always isPage=True
      - Must have a linked Page
      - No tags or carousel in the form (kept simple)
    """

    list_display = ("title", "slug", "page_link", "created_at")
    list_filter = ("page",)
    autocomplete_fields = ["page"]
    exclude = ("isPage", "tags", "isCarousel")

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "description", "page"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(isPage=True).select_related("page").prefetch_related("texts", "images")

    def save_model(self, request, obj, form, change):
        # Force this to always be page content
        obj.isPage = True
        # No tags or carousel
        obj.isCarousel = False
        super().save_model(request, obj, form, change)


# ---------- NEWS CONTENT ADMIN (only isPage=False) ----------


@admin.register(NewsContent)
class NewsContentAdmin(BaseContentAdmin):
    """
    For news content:
      - Always isPage=False
      - No page link
      - Can have tags + carousel
    """

    list_display = ("title", "slug", "isCarousel", "tags_list", "created_at")
    list_filter = ("tags", "isCarousel")
    autocomplete_fields = ["tags"]
    exclude = ("isPage", "page")

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "description"),
        }),
        ("Мэдээний тохиргоо", {
            "fields": ("isCarousel", "tags"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(isPage=False).prefetch_related("tags", "texts", "images")

    def save_model(self, request, obj, form, change):
        # Force this to always be news content
        obj.isPage = False
        # No page relation
        obj.page = None
        super().save_model(request, obj, form, change)


# ---------- VIDEO URL ADMIN ----------


@admin.register(VideoUrl)
class VideoUrlAdmin(admin.ModelAdmin):
    list_display = ("title", "video_source_display", "has_file", "has_url")
    search_fields = ("title", "url")
    list_filter = ("video_file",)
    list_per_page = 25
    ordering = ("title",)

    def video_source_display(self, obj):
        if obj.video_file:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">Файлаас ({} байршил)</a>',
                obj.video_file.url,
                obj.video_file.name,
            )
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">Гадаад холбоос</a>',
                obj.url,
            )
        return "Видео эх сурвалж байхгүй"

    video_source_display.short_description = "Видео эх сурвалж"

    def has_file(self, obj):
        return bool(obj.video_file)

    has_file.boolean = True
    has_file.short_description = "Файлтай?"

    def has_url(self, obj):
        return bool(obj.url)

    has_url.boolean = True
    has_url.short_description = "URL байна?"
