import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class NewsCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True, related_name='subcategories')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "News Category"
        verbose_name_plural = "News Categories"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    category = models.ForeignKey(
        NewsCategory, on_delete=models.SET_NULL, null=True, related_name='news')
    tags = models.ManyToManyField(Tag, related_name='news', blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Page(models.Model):
    TEMPLATE_CHOICES = [
        ('standard', 'Standard'),
        ('homepage', 'Homepage'),
        ('contact', 'Contact'),
        ('admissions', 'Admissions'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    body = models.TextField(help_text="Plain text content")
    template = models.CharField(
        max_length=50, choices=TEMPLATE_CHOICES, default='standard')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PageImage(models.Model):
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='page_images/')
    text = models.TextField(
        blank=True, help_text="Description or caption for the image")
    order = models.IntegerField(default=0, help_text="Order of display")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.page.title} ({self.order})"
