# your_app/context_processors.py
from django.urls import reverse
from .models import Page, Content, Tag, VideoUrl, NewsContent  # import NewsContent proxy


def admin_counts(request):
    if not request.path.startswith("/admin"):
        return {}

    # --- counts ---
    pages_qs = Page.objects.all()
    page_count = pages_qs.count()
    page_published_count = pages_qs.filter(is_published=True).count()

    contents_qs = Content.objects.all()
    pagecontent_count = contents_qs.filter(isPage=True).count()
    newscontent_count = contents_qs.filter(isPage=False).count()

    tag_count = Tag.objects.count()
    video_count = VideoUrl.objects.count()

    # --- latest objects ---
    latest_pages = list(pages_qs.order_by("-created_at")[:5])
    latest_news = list(contents_qs.filter(isPage=False).order_by("-created_at")[:5])

    # ------- PAGE admin URLs -------
    page_app = Page._meta.app_label
    page_model = Page._meta.model_name

    page_change_name = f"admin:{page_app}_{page_model}_change"
    page_list_url = reverse(f"admin:{page_app}_{page_model}_changelist")
    page_add_url = reverse(f"admin:{page_app}_{page_model}_add")

    for p in latest_pages:
        p.admin_url = reverse(page_change_name, args=[p.pk])

    # ------- NEWS admin URLs (use NewsContent proxy) -------
    news_app = NewsContent._meta.app_label
    news_model = NewsContent._meta.model_name  # "newscontent"

    news_change_name = f"admin:{news_app}_{news_model}_change"
    news_list_url = reverse(f"admin:{news_app}_{news_model}_changelist")
    news_add_url = reverse(f"admin:{news_app}_{news_model}_add")

    for n in latest_news:
        # n is a Content instance, but admin URL uses NewsContent model name
        n.admin_url = reverse(news_change_name, args=[n.pk])

    return {
        "page_count": page_count,
        "page_published_count": page_published_count,
        "pagecontent_count": pagecontent_count,
        "newscontent_count": newscontent_count,
        "tag_count": tag_count,
        "video_count": video_count,
        "latest_pages": latest_pages,
        "latest_news": latest_news,
        "page_list_url": page_list_url,
        "page_add_url": page_add_url,
        "news_list_url": news_list_url,
        "news_add_url": news_add_url,
    }
